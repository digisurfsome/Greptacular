/**
 * WorkspaceUserGuide - Floating, draggable, resizable user guide panel.
 *
 * Provides tabbed documentation sections for the workspace chat feature,
 * a "Walkie-Talkie" tab explaining the WebSocket communication system,
 * and a full-featured "Notes" tab with multi-note management (search,
 * tags, sort, create/edit/delete) persisted to localStorage.
 *
 * Position, size, and notes all persist across sessions via localStorage.
 */

import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import {
  X,
  Minus,
  Maximize2,
  BookOpen,
  GripHorizontal,
  Plus,
  ArrowLeft,
  Trash2,
  Search,
  ChevronDown,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STORAGE_KEY_POS = 'workspace-guide-pos'
const STORAGE_KEY_SIZE = 'workspace-guide-size'
const STORAGE_KEY_NOTES_V2 = 'workspace-notes-v2'

const MIN_WIDTH = 340
const MIN_HEIGHT = 280
const DEFAULT_WIDTH = 460
const DEFAULT_HEIGHT = 520

/** Debounce delay for auto-saving notes (ms) */
const AUTOSAVE_DELAY_MS = 500

/** How many characters of content to show in the note card preview */
const PREVIEW_CHAR_LIMIT = 80

const TAB_IDS = [
  'overview',
  'sidebar',
  'chat',
  'panels',
  'splitswarm',
  'shortcuts',
  'reference',
  'notes',
] as const

type TabId = (typeof TAB_IDS)[number]

const TAB_LABELS: Record<TabId, string> = {
  overview: 'Overview',
  sidebar: 'Sidebar',
  chat: 'Chat',
  panels: 'Panels',
  splitswarm: 'Split & Swarm',
  shortcuts: 'Shortcuts',
  reference: 'Reference',
  notes: 'Notes',
}

// Platform detection for keyboard shortcut labels
const isMac = typeof navigator !== 'undefined' && navigator.platform.includes('Mac')
const mod = isMac ? 'Cmd' : 'Ctrl'

// ---------------------------------------------------------------------------
// Note data model
// ---------------------------------------------------------------------------

interface Note {
  id: string
  title: string
  tags: string[]
  content: string
  createdAt: string
  updatedAt: string
}

type NotesSortKey = 'updatedAt' | 'createdAt' | 'titleAZ' | 'titleZA'

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
// ID generation (no external deps)
// ---------------------------------------------------------------------------

/** Generate a unique ID using timestamp + random suffix. */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

// ---------------------------------------------------------------------------
// Relative time formatting
// ---------------------------------------------------------------------------

/** Format an ISO date string as a human-friendly relative time. */
function formatRelativeTime(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diffMs = now - then

  if (diffMs < 0) return 'just now'

  const seconds = Math.floor(diffMs / 1000)
  if (seconds < 60) return '< 1 min ago'

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`

  const days = Math.floor(hours / 24)
  if (days === 1) return 'yesterday'

  // Fall back to a short date string for older notes
  const d = new Date(iso)
  const month = d.toLocaleString('en-US', { month: 'short' })
  const day = d.getDate()
  return `${month} ${day}`
}

// ---------------------------------------------------------------------------
// Tag color helper
// ---------------------------------------------------------------------------

/** Deterministic tag color from a small palette. */
const TAG_COLORS = [
  'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300',
  'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
  'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
]

function tagColorClass(tag: string): string {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = (hash * 31 + tag.charCodeAt(i)) | 0
  }
  return TAG_COLORS[Math.abs(hash) % TAG_COLORS.length]
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

// ---------------------------------------------------------------------------
// Section heading helper
// ---------------------------------------------------------------------------

function SectionHeading({ children }: { children: React.ReactNode }): React.JSX.Element {
  return <p className="font-semibold text-foreground text-[11px] pt-1">{children}</p>
}

// ---------------------------------------------------------------------------
// Overview Tab  (Manual Sections 1-2: Page Layout + Navigation Bar)
// ---------------------------------------------------------------------------

function OverviewTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <SectionHeading>Page Layout</SectionHeading>
      <p>The Workspace is a full-screen three-column layout with a thin navigation bar across the top.</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Left &mdash; Sidebar</span> (272px, collapsible): conversations, search, categories</li>
        <li><span className="text-foreground font-medium">Center &mdash; Chat Area</span> (flexible): active conversation or Split View panels</li>
        <li><span className="text-foreground font-medium">Right &mdash; Library</span> (288px, collapsible): file library, repos, walkie-talkie log</li>
      </ul>
      <p>
        Optional panels: <span className="text-foreground font-medium">Swarm</span> (320px, between chat and library),{' '}
        <span className="text-foreground font-medium">Token Log</span> (320px, left of chat), and{' '}
        <span className="text-foreground font-medium">Countdown Timer Bar</span> (conditional, below nav).
      </p>

      <SectionHeading>Navigation Bar</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Back to AutoForge</span> &mdash; returns to the main dashboard</li>
        <li><span className="text-foreground font-medium">Git Activity (G)</span> &mdash; blinking badge showing recent commits; click to see last 10</li>
        <li><span className="text-foreground font-medium">CI Status</span> &mdash; pipeline indicator (idle/running/passed/failed); auto-merge countdown when CI passes</li>
        <li><span className="text-foreground font-medium">Split</span> &mdash; toggles three-panel Research / PRD / Coder layout</li>
        <li><span className="text-foreground font-medium">Swarm</span> &mdash; toggles the concurrent agent pipeline panel</li>
        <li><span className="text-foreground font-medium">Roles</span> &mdash; navigates to the Agent Role Library</li>
        <li><span className="text-foreground font-medium">Dashboard</span> &mdash; navigates to the Multi-session Dashboard</li>
        <li><span className="text-foreground font-medium">Guide</span> &mdash; opens this panel</li>
        <li><span className="text-foreground font-medium">Keyboard icon</span> &mdash; shows keyboard shortcuts (or press <Kbd>?</Kbd>)</li>
      </ul>

      <SectionHeading>Split View extras (visible when Split is on)</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">R / P / C / All</span> &mdash; quick-focus a single panel or show all three</li>
        <li><span className="text-foreground font-medium">Auto</span> &mdash; auto-forward PRD output to the Coder panel</li>
      </ul>

      <SectionHeading>Context Window</SectionHeading>
      <p>Up to <span className="text-foreground font-medium">1M tokens</span> of context. The budget bar shows allocation:</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="font-medium text-foreground/80">Dark</span> &mdash; conversation summaries</li>
        <li><span className="font-medium text-foreground/80">Medium</span> &mdash; recent messages</li>
        <li><span className="font-medium text-primary">Blue</span> &mdash; library files</li>
        <li><span className="font-medium text-green-600 dark:text-green-400">Green</span> &mdash; repo files</li>
      </ul>
      <p>
        Turns <span className="text-orange-500 font-medium">orange at 80%</span> and{' '}
        <span className="text-destructive font-medium">red at 90%</span>.
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sidebar Tab  (Manual Sections 3-5: New Chat, Conversations, Categories)
// ---------------------------------------------------------------------------

function SidebarTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <SectionHeading>New Chat Form</SectionHeading>
      <p>Click <span className="text-foreground font-medium">+ New Chat</span> to expand the creation form:</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Name</span> &mdash; optional; auto-focused, <Kbd>Enter</Kbd> to submit, <Kbd>Esc</Kbd> to cancel</li>
        <li><span className="text-foreground font-medium">Folder</span> &mdash; assign to a category</li>
        <li><span className="text-foreground font-medium">Attach Repository</span> &mdash; toggle on to pick a GitHub repo (clones it and sets working dir)</li>
        <li><span className="text-foreground font-medium">Model pills</span> &mdash; Opus 1M, Sonnet 1M, Opus 200K (colors: blue, violet, zinc). Other providers show their own models.</li>
        <li><span className="text-foreground font-medium">Thinking Effort</span> &mdash; Low / Medium / High (only active on Opus 1M)</li>
      </ul>

      <SectionHeading>Search</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li>Under 3 characters &mdash; client-side title filter</li>
        <li>3+ characters &mdash; server-side full-text search with excerpts (300ms debounce)</li>
      </ul>

      <SectionHeading>Conversation List</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li>Grouped by category with collapsible headers and count badges</li>
        <li>Pinned items appear in a special group at the top</li>
        <li><span className="text-foreground font-medium">Model badge</span> (top-right of row) &mdash; click to cycle through model/context combos</li>
        <li>
          Activity indicators:{' '}
          <span className="text-cyan-500 font-medium">cyan pulse</span> = streaming,{' '}
          <span className="text-yellow-500 font-medium">yellow</span> = waiting,{' '}
          <span className="text-green-500 font-medium">green dot</span> = completed,{' '}
          <span className="text-red-500 font-medium">red</span> = failed
        </li>
        <li>Hover actions: <span className="text-foreground font-medium">Folder</span> (move + attach repo), <span className="text-foreground font-medium">Pin</span>, <span className="text-foreground font-medium">Delete</span></li>
      </ul>

      <SectionHeading>Select Mode</SectionHeading>
      <p>Click the checkbox icon in the header to enter select mode. Check conversations, then use <span className="text-foreground font-medium">All/None</span> toggle or <span className="text-destructive font-medium">Delete (N)</span> for bulk operations.</p>

      <SectionHeading>Category Management</SectionHeading>
      <p>
        Click <span className="text-foreground font-medium">Manage Categories</span> at the bottom of the sidebar.
        Create, rename, reorder (up/down arrows), change colors, or delete categories.
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Chat Tab  (Manual Sections 6-9: Header, Extensions, Content, Input)
// ---------------------------------------------------------------------------

function ChatTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <SectionHeading>Chat Header</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Title</span> &mdash; click to edit inline; pencil icon on hover</li>
        <li><span className="text-foreground font-medium">Category dropdown</span> &mdash; re-categorize the conversation</li>
        <li><span className="text-foreground font-medium">Tags</span> &mdash; colored chips; click + to add, X to remove</li>
        <li><span className="text-foreground font-medium">Git branch</span> &mdash; shows current branch; rename non-protected branches via pencil icon</li>
        <li><span className="text-foreground font-medium">Repo / PR badges</span> &mdash; open GitHub repo or pull request in a new tab</li>
        <li>
          <span className="text-foreground font-medium">Connection dot</span>:{' '}
          <span className="text-green-500">green</span> = connected,{' '}
          <span className="text-yellow-500">yellow</span> = connecting,{' '}
          <span className="text-red-500">red</span> = disconnected
        </li>
      </ul>

      <SectionHeading>Header Extensions</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Active Model badge</span> &mdash; shows model, context, and API cost</li>
        <li><span className="text-foreground font-medium">Token Log toggle</span> &mdash; Auto (show during streaming) | On | Off</li>
        <li><span className="text-foreground font-medium">Three-dot menu (&hellip;)</span>:</li>
      </ul>
      <ul className="list-disc pl-8 space-y-1">
        <li><span className="text-foreground font-medium">Fork Chat</span> &mdash; branch from any message into a new conversation</li>
        <li><span className="text-foreground font-medium">Inject from Chat</span> &mdash; pull messages from another conversation (two-step picker)</li>
        <li><span className="text-foreground font-medium">Export as Markdown</span> &mdash; download conversation as <code className="text-[10px] bg-muted px-1 rounded">.md</code></li>
      </ul>

      <SectionHeading>Walkie-Talkie</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Settings gear</span> &mdash; opens panel with check frequency, wait timeout, and auto-reply toggle</li>
        <li><span className="text-foreground font-medium">Live/Waiting indicator</span> &mdash; pulsing amber dot when agent is active</li>
        <li><span className="text-foreground font-medium">WT input bar</span> &mdash; send messages to a running agent mid-session</li>
      </ul>

      <SectionHeading>Chat Content</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li>Messages display with user/assistant/system roles</li>
        <li>Auto-summary pin appears after 50 messages</li>
        <li>Disconnection banner with retry link if WebSocket drops</li>
        <li>Usage dashboard (expandable) for session cost tracking</li>
        <li>Countdown timer bar when agent waits for input</li>
      </ul>

      <SectionHeading>Composing Messages</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li><Kbd>Enter</Kbd> to send, <Kbd>Shift+Enter</Kbd> for a new line</li>
        <li>Drag-and-drop files or images onto the input area</li>
        <li><span className="text-foreground font-medium">Paperclip</span> &mdash; attach files, <span className="text-foreground font-medium">Image+</span> &mdash; attach images</li>
        <li><span className="text-foreground font-medium">BookOpen</span> &mdash; pick library files to include as context</li>
        <li><Kbd>{mod}+V</Kbd> to paste images from clipboard</li>
        <li>Drafts are auto-saved while you type</li>
      </ul>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Panels Tab  (Manual Sections 10, 14: Library/Repos/WT + Token Log)
// ---------------------------------------------------------------------------

function PanelsTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <SectionHeading>Right Panel &mdash; Library</SectionHeading>
      <p>Three tabs at the top: <span className="text-foreground font-medium">Library</span>, <span className="text-foreground font-medium">Repos</span>, <span className="text-foreground font-medium">WT</span>. Collapse with the <code className="text-[10px] bg-muted px-1 rounded">&gt;&gt;</code> button.</p>

      <p className="font-semibold text-foreground text-[11px] pt-0.5">Library tab</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Upload / Paste</span> buttons to add files</li>
        <li>Hierarchical folder browser &mdash; click folders to navigate, click files to preview</li>
      </ul>

      <p className="font-semibold text-foreground text-[11px] pt-0.5">Repos tab</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Connect Repository</span> to link a GitHub repo</li>
        <li>Expandable file browser per repo; click files to preview content</li>
      </ul>

      <p className="font-semibold text-foreground text-[11px] pt-0.5">Walkie-Talkie (WT) tab</p>
      <ul className="list-disc pl-4 space-y-1">
        <li>Chronological log of all WT messages (user, agent, system)</li>
        <li>Color-coded: amber (you), primary (agent), gray (system)</li>
        <li>Auto-scrolls to latest entry</li>
      </ul>

      <SectionHeading>Library Modals</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Library Picker</span> &mdash; browse and multi-select files to attach to a message (BookOpen button in chat input)</li>
        <li><span className="text-foreground font-medium">Save to Library</span> &mdash; save an assistant response as a library file (filename, folder, tags)</li>
      </ul>

      <SectionHeading>Token Log Panel (left side)</SectionHeading>
      <p>A 320px panel to the left of chat, controlled by the 3-state toggle (Auto/On/Off).</p>
      <ul className="list-disc pl-4 space-y-1">
        <li>
          Event types:{' '}
          <span className="text-cyan-500 font-medium">assistant_turn</span>,{' '}
          <span className="text-yellow-500 font-medium">tool_call</span>,{' '}
          <span className="text-orange-500 font-medium">tool_result</span>,{' '}
          <span className="text-green-500 font-medium">result_summary</span>
        </li>
        <li>Each entry shows token counts, cost, duration, cumulative cost</li>
        <li>Header buttons: Download (JSON), Clear, Close</li>
        <li>Summary section with total cost, tokens, and cache info</li>
      </ul>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Split & Swarm Tab  (Manual Sections 11-13: Split View, Passoff, Swarm)
// ---------------------------------------------------------------------------

function SplitSwarmTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <SectionHeading>Split View &mdash; Three-Panel Layout</SectionHeading>
      <p>Activate via the <span className="text-foreground font-medium">Split</span> button in the nav bar. Replaces the single chat with three resizable, independently collapsible panels.</p>

      <ul className="list-disc pl-4 space-y-1">
        <li>
          <span className="text-emerald-500 font-medium">Research</span> (left) &mdash; 200K context, emerald accents.
          Has a <span className="text-foreground font-medium">Copy to Passoff</span> button on assistant messages.
        </li>
        <li>
          <span className="text-violet-500 font-medium">PRD Builder</span> (center) &mdash; 1M context for Opus, violet accents.
          Two tabs: <span className="text-foreground font-medium">Chat</span> and <span className="text-foreground font-medium">Passoff</span> (structured editor).
        </li>
        <li>
          <span className="text-cyan-500 font-medium">Coder</span> (right) &mdash; 1M context for Opus, cyan accents.
          Receives auto-forwarded content from PRD Builder.
        </li>
      </ul>
      <p>Collapsed panels appear as thin vertical bars with rotated labels &mdash; click to expand.</p>

      <SectionHeading>Passoff Editor</SectionHeading>
      <p>Located in the PRD Builder&apos;s <span className="text-foreground font-medium">Passoff</span> tab.</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Preamble</span> &mdash; free-form context text at the top</li>
        <li><span className="text-foreground font-medium">Section cards</span> &mdash; title + content, drag-and-drop reorder, collapse/expand</li>
        <li><span className="text-foreground font-medium">+ Add Section</span> to add new sections</li>
        <li><span className="text-foreground font-medium">Send to Execute</span> (violet button) &mdash; builds markdown from all sections and injects it into the PRD Chat</li>
      </ul>

      <SectionHeading>Swarm Panel</SectionHeading>
      <p>Toggle via <span className="text-foreground font-medium">Swarm</span> button. A 320px panel for managing concurrent autonomous agents.</p>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">Task Input</span> &mdash; describe the task before starting the swarm</li>
        <li><span className="text-foreground font-medium">Pipeline Stages</span> &mdash; cards showing Research, Plan, Implement, Test, Review stages with status badges</li>
        <li><span className="text-foreground font-medium">Shared Files</span> &mdash; files generated by the swarm, clickable for preview</li>
        <li>Per-stage walkie-talkie injection to send guidance to individual agents</li>
        <li>Status badge in header: RUNNING / COMPLETED / FAILED / STOPPED</li>
      </ul>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Shortcuts Tab  (Manual Section 15: Keyboard Shortcuts)
// ---------------------------------------------------------------------------

function ShortcutsTab(): React.JSX.Element {
  const shortcuts = [
    { key: `${mod}+N`, desc: 'New conversation' },
    { key: `${mod}+B`, desc: 'Toggle sidebar' },
    { key: `${mod}+L`, desc: 'Toggle library panel' },
    { key: `${mod}+F`, desc: 'Focus search' },
    { key: `${mod}+E`, desc: 'Export current chat as Markdown' },
    { key: '/', desc: 'Focus chat input' },
    { key: '1', desc: 'Toggle Research panel (Split View)' },
    { key: '2', desc: 'Toggle PRD Builder panel (Split View)' },
    { key: '3', desc: 'Toggle Coder panel (Split View)' },
    { key: '?', desc: 'Show keyboard shortcuts modal' },
    { key: 'Enter', desc: 'Send message' },
    { key: 'Shift+Enter', desc: 'New line in input' },
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

// ---------------------------------------------------------------------------
// Reference Tab  (Manual Sections 16-18: Modals, Errors, Persistence)
// ---------------------------------------------------------------------------

function ReferenceTab(): React.JSX.Element {
  return (
    <div className="space-y-2 text-xs text-muted-foreground">
      <SectionHeading>All Modals</SectionHeading>
      <ul className="list-disc pl-4 space-y-0.5">
        <li><span className="text-foreground font-medium">Keyboard Shortcuts</span> &mdash; <Kbd>?</Kbd> or keyboard icon</li>
        <li><span className="text-foreground font-medium">User Guide &amp; Notes</span> &mdash; Guide button in nav bar</li>
        <li><span className="text-foreground font-medium">Category Manager</span> &mdash; Manage Categories in sidebar</li>
        <li><span className="text-foreground font-medium">Fork Chat</span> &mdash; &hellip; menu &gt; Fork Chat</li>
        <li><span className="text-foreground font-medium">Inject from Chat</span> &mdash; &hellip; menu &gt; Inject from Chat</li>
        <li><span className="text-foreground font-medium">File Upload / Paste</span> &mdash; Upload/Paste in Library tab</li>
        <li><span className="text-foreground font-medium">Repo Connector</span> &mdash; Connect Repository in Repos tab</li>
        <li><span className="text-foreground font-medium">Library Picker</span> &mdash; BookOpen in chat input</li>
        <li><span className="text-foreground font-medium">Save to Library</span> &mdash; Save to Library on assistant messages</li>
      </ul>

      <SectionHeading>Error States</SectionHeading>
      <ul className="list-disc pl-4 space-y-1">
        <li><span className="text-foreground font-medium">No working directory</span> &mdash; Git/CI widgets hidden; Swarm shows a warning</li>
        <li><span className="text-foreground font-medium">WebSocket failure</span> &mdash; red dot + disconnection banner with retry link</li>
        <li><span className="text-foreground font-medium">Empty library</span> &mdash; folder browser shows empty state</li>
        <li><span className="text-foreground font-medium">No conversations</span> &mdash; sidebar shows empty prompt</li>
        <li><span className="text-foreground font-medium">Streaming interrupted</span> &mdash; conversation preserved; reconnect shows prior messages</li>
      </ul>

      <SectionHeading>Data Persistence</SectionHeading>
      <table className="w-full text-[10px] mt-1">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-0.5 pr-2 font-medium">Data</th>
            <th className="text-left py-0.5 font-medium">Where</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b border-border/50">
            <td className="py-1 pr-2">Panel states, model selection, drafts</td>
            <td className="py-1">localStorage (per-browser)</td>
          </tr>
          <tr className="border-b border-border/50">
            <td className="py-1 pr-2">Guide position, size, notes</td>
            <td className="py-1">localStorage (per-browser)</td>
          </tr>
          <tr className="border-b border-border/50">
            <td className="py-1 pr-2">Walkie-talkie settings</td>
            <td className="py-1">Server (Settings API)</td>
          </tr>
          <tr className="border-b border-border/50">
            <td className="py-1 pr-2">Conversations, messages, categories</td>
            <td className="py-1">Server (SQLite)</td>
          </tr>
          <tr className="border-b border-border/50">
            <td className="py-1 pr-2">Library files &amp; folders</td>
            <td className="py-1">Server (SQLite + filesystem)</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Notes Tab - full-featured multi-note management
// ---------------------------------------------------------------------------

/**
 * Load all notes from localStorage, falling back to an empty array.
 * Handles graceful migration: if the legacy single-string key exists,
 * it is ignored (the user starts fresh with the v2 format).
 */
function loadNotes(): Note[] {
  return loadJSON<Note[]>(STORAGE_KEY_NOTES_V2, [])
}

function saveNotes(notes: Note[]): void {
  saveJSON(STORAGE_KEY_NOTES_V2, notes)
}

function NotesTab(): React.JSX.Element {
  // ---- State ----
  const [notes, setNotes] = useState<Note[]>(loadNotes)
  const [view, setView] = useState<'list' | 'edit'>('list')
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTag, setActiveTag] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<NotesSortKey>('updatedAt')
  const [showSaved, setShowSaved] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)

  const savedTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (savedTimer.current) clearTimeout(savedTimer.current)
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current)
    }
  }, [])

  // Always reset to list view when the Notes tab mounts
  useEffect(() => {
    setView('list')
    setEditingNoteId(null)
  }, [])

  // ---- Derived data ----

  /** All unique tags across every note */
  const allTags = useMemo(() => {
    const tagSet = new Set<string>()
    for (const n of notes) {
      for (const t of n.tags) tagSet.add(t)
    }
    return Array.from(tagSet).sort((a, b) => a.localeCompare(b))
  }, [notes])

  /** Filtered and sorted notes for the list view */
  const filteredNotes = useMemo(() => {
    const q = searchQuery.toLowerCase().trim()
    let result = notes

    // Filter by active tag
    if (activeTag) {
      result = result.filter((n) => n.tags.includes(activeTag))
    }

    // Filter by search query (title + tags)
    if (q) {
      result = result.filter(
        (n) =>
          n.title.toLowerCase().includes(q) ||
          n.tags.some((t) => t.toLowerCase().includes(q)),
      )
    }

    // Sort
    const sorted = [...result]
    switch (sortKey) {
      case 'updatedAt':
        sorted.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
        break
      case 'createdAt':
        sorted.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
        break
      case 'titleAZ':
        sorted.sort((a, b) => a.title.localeCompare(b.title))
        break
      case 'titleZA':
        sorted.sort((a, b) => b.title.localeCompare(a.title))
        break
    }

    return sorted
  }, [notes, searchQuery, activeTag, sortKey])

  /** The note currently being edited */
  const editingNote = useMemo(
    () => (editingNoteId ? notes.find((n) => n.id === editingNoteId) ?? null : null),
    [notes, editingNoteId],
  )

  // ---- Helpers ----

  /** Persist notes and flash the saved indicator */
  const persistAndFlashSaved = useCallback((updated: Note[]) => {
    saveNotes(updated)
    setShowSaved(true)
    if (savedTimer.current) clearTimeout(savedTimer.current)
    savedTimer.current = setTimeout(() => setShowSaved(false), 1500)
  }, [])

  /** Create a new note and switch to edit view */
  const handleCreateNote = useCallback(() => {
    const now = new Date().toISOString()
    const newNote: Note = {
      id: generateId(),
      title: 'Untitled Note',
      tags: [],
      content: '',
      createdAt: now,
      updatedAt: now,
    }
    const updated = [newNote, ...notes]
    setNotes(updated)
    saveNotes(updated)
    setEditingNoteId(newNote.id)
    setView('edit')
  }, [notes])

  /** Open a note in edit view */
  const handleOpenNote = useCallback((id: string) => {
    setEditingNoteId(id)
    setView('edit')
  }, [])

  /** Go back to list view */
  const handleBackToList = useCallback(() => {
    setView('list')
    setEditingNoteId(null)
  }, [])

  /** Delete a note by id */
  const handleDeleteNote = useCallback(
    (id: string) => {
      const updated = notes.filter((n) => n.id !== id)
      setNotes(updated)
      saveNotes(updated)
      setConfirmDeleteId(null)
      // If we were editing this note, go back to list
      if (editingNoteId === id) {
        setView('list')
        setEditingNoteId(null)
      }
    },
    [notes, editingNoteId],
  )

  /** Update a field on the editing note with debounced autosave */
  const handleUpdateNote = useCallback(
    (field: 'title' | 'content' | 'tags', value: string | string[]) => {
      if (!editingNoteId) return

      const now = new Date().toISOString()
      const updated = notes.map((n) =>
        n.id === editingNoteId ? { ...n, [field]: value, updatedAt: now } : n,
      )
      setNotes(updated)

      // Debounced persist
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current)
      autosaveTimer.current = setTimeout(() => {
        persistAndFlashSaved(updated)
      }, AUTOSAVE_DELAY_MS)
    },
    [notes, editingNoteId, persistAndFlashSaved],
  )

  // ---- Render: List View ----

  if (view === 'list') {
    return (
      <div className="flex flex-col h-full gap-2">
        {/* Search + New button row */}
        <div className="flex gap-1.5 items-center">
          <div className="relative flex-1">
            <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              className="w-full pl-7 pr-2 py-1.5 text-xs bg-background border border-border rounded focus:outline-none focus:ring-1 focus:ring-ring placeholder:text-muted-foreground"
              placeholder="Search notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button variant="default" size="xs" onClick={handleCreateNote} title="New Note">
            <Plus size={12} />
            <span className="text-[10px]">New</span>
          </Button>
        </div>

        {/* Tag filter chips */}
        {allTags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setActiveTag((prev) => (prev === tag ? null : tag))}
                className={`px-1.5 py-0.5 text-[9px] rounded-full border transition-colors ${
                  activeTag === tag
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-muted text-muted-foreground border-border hover:bg-accent'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        )}

        {/* Sort dropdown */}
        <div className="flex items-center gap-1">
          <label className="text-[10px] text-muted-foreground">Sort:</label>
          <div className="relative">
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as NotesSortKey)}
              className="appearance-none text-[10px] bg-background border border-border rounded pl-1.5 pr-5 py-0.5 text-foreground focus:outline-none focus:ring-1 focus:ring-ring cursor-pointer"
            >
              <option value="updatedAt">Last Modified</option>
              <option value="createdAt">Created</option>
              <option value="titleAZ">Title A-Z</option>
              <option value="titleZA">Title Z-A</option>
            </select>
            <ChevronDown size={10} className="absolute right-1 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          </div>
        </div>

        {/* Note cards list */}
        <div className="flex-1 overflow-y-auto space-y-1.5 min-h-0">
          {filteredNotes.length === 0 && (
            <div className="text-center py-6 text-xs text-muted-foreground">
              {notes.length === 0
                ? 'No notes yet. Create one to get started!'
                : 'No notes match your search.'}
            </div>
          )}

          {filteredNotes.map((note) => (
            <div
              key={note.id}
              className="group border border-border rounded p-2 bg-background hover:bg-muted/50 cursor-pointer transition-colors relative"
              onClick={() => handleOpenNote(note.id)}
            >
              <div className="flex items-start justify-between gap-1">
                <p className="text-xs font-medium text-foreground truncate flex-1">
                  {note.title || 'Untitled Note'}
                </p>
                {/* Delete button */}
                {confirmDeleteId === note.id ? (
                  <div
                    className="flex items-center gap-1 shrink-0"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      className="text-[9px] text-destructive font-medium hover:underline"
                      onClick={() => handleDeleteNote(note.id)}
                    >
                      Delete
                    </button>
                    <button
                      className="text-[9px] text-muted-foreground hover:underline"
                      onClick={() => setConfirmDeleteId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive shrink-0"
                    title="Delete note"
                    onClick={(e) => {
                      e.stopPropagation()
                      setConfirmDeleteId(note.id)
                    }}
                  >
                    <Trash2 size={12} />
                  </button>
                )}
              </div>

              {/* Tags */}
              {note.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {note.tags.map((tag) => (
                    <span
                      key={tag}
                      className={`px-1.5 py-0 text-[9px] rounded-full ${tagColorClass(tag)}`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Content preview */}
              {note.content && (
                <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                  {note.content.length > PREVIEW_CHAR_LIMIT
                    ? note.content.slice(0, PREVIEW_CHAR_LIMIT) + '...'
                    : note.content}
                </p>
              )}

              {/* Timestamp */}
              <p className="text-[9px] text-muted-foreground/70 mt-1">
                {formatRelativeTime(note.updatedAt)}
              </p>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ---- Render: Edit View ----

  if (!editingNote) {
    // Safety: should not happen, but handle gracefully
    setView('list')
    return <div />
  }

  return <NoteEditView
    note={editingNote}
    showSaved={showSaved}
    onBack={handleBackToList}
    onUpdate={handleUpdateNote}
    onDelete={() => handleDeleteNote(editingNote.id)}
  />
}

// ---------------------------------------------------------------------------
// NoteEditView - extracted for clarity
// ---------------------------------------------------------------------------

interface NoteEditViewProps {
  note: Note
  showSaved: boolean
  onBack: () => void
  onUpdate: (field: 'title' | 'content' | 'tags', value: string | string[]) => void
  onDelete: () => void
}

function NoteEditView({ note, showSaved, onBack, onUpdate, onDelete }: NoteEditViewProps): React.JSX.Element {
  const [tagInput, setTagInput] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)

  /** Add tags from the input field (comma-separated) */
  const handleAddTags = useCallback(() => {
    const newTags = tagInput
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0 && !note.tags.includes(t))

    if (newTags.length > 0) {
      onUpdate('tags', [...note.tags, ...newTags])
    }
    setTagInput('')
  }, [tagInput, note.tags, onUpdate])

  /** Remove a single tag */
  const handleRemoveTag = useCallback(
    (tag: string) => {
      onUpdate('tags', note.tags.filter((t) => t !== tag))
    },
    [note.tags, onUpdate],
  )

  return (
    <div className="flex flex-col h-full gap-2">
      {/* Header: back + delete */}
      <div className="flex items-center justify-between shrink-0">
        <button
          onClick={onBack}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft size={14} />
          <span>Back</span>
        </button>
        <div className="flex items-center gap-2">
          {showSaved && (
            <span className="text-[10px] text-muted-foreground animate-fade-in">
              Saved
            </span>
          )}
          {confirmDelete ? (
            <div className="flex items-center gap-1">
              <button
                className="text-[10px] text-destructive font-medium hover:underline"
                onClick={onDelete}
              >
                Confirm
              </button>
              <button
                className="text-[10px] text-muted-foreground hover:underline"
                onClick={() => setConfirmDelete(false)}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="text-muted-foreground hover:text-destructive transition-colors"
              title="Delete note"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Title */}
      <input
        type="text"
        className="w-full text-sm font-semibold text-foreground bg-transparent border-b border-border pb-1 focus:outline-none focus:border-primary placeholder:text-muted-foreground"
        placeholder="Note title..."
        value={note.title}
        onChange={(e) => onUpdate('title', e.target.value)}
      />

      {/* Tags display + input */}
      <div className="shrink-0">
        {note.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-1.5">
            {note.tags.map((tag) => (
              <span
                key={tag}
                className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] rounded-full ${tagColorClass(tag)}`}
              >
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="hover:opacity-70 ml-0.5"
                  title={`Remove tag "${tag}"`}
                >
                  <X size={8} />
                </button>
              </span>
            ))}
          </div>
        )}
        <input
          type="text"
          className="w-full text-[10px] bg-background border border-border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-ring placeholder:text-muted-foreground"
          placeholder="Add tags (comma-separated, press Enter)..."
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              handleAddTags()
            }
          }}
          onBlur={handleAddTags}
        />
      </div>

      {/* Content */}
      <textarea
        className="flex-1 w-full resize-none bg-background border border-border rounded p-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring min-h-0"
        placeholder="Write your note..."
        value={note.content}
        onChange={(e) => onUpdate('content', e.target.value)}
      />
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
    case 'sidebar':
      return <SidebarTab />
    case 'chat':
      return <ChatTab />
    case 'panels':
      return <PanelsTab />
    case 'splitswarm':
      return <SplitSwarmTab />
    case 'shortcuts':
      return <ShortcutsTab />
    case 'reference':
      return <ReferenceTab />
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
