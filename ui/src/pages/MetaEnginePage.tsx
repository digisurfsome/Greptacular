/**
 * MetaEnginePage - Metaprogram Engine UI for training, generating, and
 * exporting audience-adapted copy based on NLP metaprograms.
 *
 * Dark theme matching CLI Scripter (bg-[#0a0a0a], orange/cyan/green accents).
 * Full-width layout with side-by-side panels.
 *
 * Four tabs:
 *   1. Upload / Ingest   - YouTube URL, file upload, text paste
 *   2. Training Library   - Browse accumulated examples, patterns, scenarios
 *   3. Writing Engine     - Generate adapted copy for a profile
 *   4. Output / Export    - Browse and export generated topics
 */

import { useState, useCallback, useRef, useEffect, type DragEvent, type ChangeEvent } from 'react'
import {
  ArrowLeft,
  Upload,
  Brain,
  PenTool,
  Download,
  Youtube,
  FileAudio,
  FileText,
  Send,
  RefreshCw,
  Loader2,
  Filter,
  Copy,
  CheckCircle2,
  XCircle,
  Sparkles,
  Layers,
  Search,
  Settings,
  StickyNote,
  Trash2,
  Plus,
  Eye,
  EyeOff,
  FolderOpen,
  Save,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

// ============================================================================
// Types
// ============================================================================

type TabId = 'ingest' | 'library' | 'writing' | 'export' | 'notes' | 'settings'

interface MetaEngineNote {
  id: string
  label: string
  content: string
  created_at: string
  updated_at: string
}

interface MetaEngineSettings {
  workspaceFolder: string
  openaiApiKey: string
  defaultChannel: string
  defaultTone: string
  autoIngest: boolean
}

interface IngestResult {
  source: string
  status: 'success' | 'error' | 'processing'
  message: string
  examples_added?: number
  patterns_added?: number
  /** Progress bar percentage (0-100) while processing */
  _progressPct?: number
}

interface LibraryStats {
  sources: number
  examples: number
  patterns: number
  scenarios: number
}

interface TrainingExample {
  id: string
  metaprogram: string
  pole: string
  text: string
  source: string
}

interface TrainingPattern {
  id: string
  metaprogram: string
  pattern: string
  frequency: number
}

interface CoachingScenario {
  id: string
  title: string
  metaprogram: string
  scenario: string
}

interface GeneratedOutput {
  topic: string
  profile: string
  channel: string
  tone: string
  content: string
  created_at: string
}

interface OutputTopic {
  slug: string
  topic: string
  output_count: number
  outputs: GeneratedOutput[]
}

// ============================================================================
// Constants
// ============================================================================

const API_BASE = '/api'

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'ingest', label: 'Upload / Ingest', icon: <Upload size={14} /> },
  { id: 'library', label: 'Training Library', icon: <Brain size={14} /> },
  { id: 'writing', label: 'Writing Engine', icon: <PenTool size={14} /> },
  { id: 'export', label: 'Output / Export', icon: <Download size={14} /> },
  { id: 'notes', label: 'Notes', icon: <StickyNote size={14} /> },
  { id: 'settings', label: 'Settings', icon: <Settings size={14} /> },
]

const CHANNELS = ['general', 'instagram', 'email', 'landing_page', 'shorts', 'x', 'dm', 'ad']
const TONES = ['conversational', 'professional', 'casual', 'urgent']

const DEFAULT_SETTINGS: MetaEngineSettings = {
  workspaceFolder: '',
  openaiApiKey: '',
  defaultChannel: CHANNELS[0],
  defaultTone: TONES[0],
  autoIngest: false,
}

const SETTINGS_STORAGE_KEY = 'metaengine-settings'
const NOTES_STORAGE_KEY = 'metaengine-notes'

/** Deterministic HSL color from a string label */
function labelColor(label: string): string {
  let hash = 0
  for (let i = 0; i < label.length; i++) {
    hash = label.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = ((hash % 360) + 360) % 360
  return `hsl(${hue}, 60%, 55%)`
}

const METAPROGRAM_OPTIONS = [
  { value: '', label: 'All metaprograms' },
  { value: 'motivation', label: 'Motivation Direction' },
  { value: 'reference', label: 'Frame of Reference' },
  { value: 'work_style', label: 'Work Style' },
  { value: 'chunk_size', label: 'Chunk Size' },
  { value: 'action', label: 'Action Filter' },
]

const POLE_OPTIONS: Record<string, { value: string; label: string }[]> = {
  motivation: [
    { value: 'toward', label: 'Toward' },
    { value: 'away_from', label: 'Away From' },
  ],
  reference: [
    { value: 'internal', label: 'Internal' },
    { value: 'external', label: 'External' },
  ],
  work_style: [
    { value: 'options', label: 'Options' },
    { value: 'procedures', label: 'Procedures' },
  ],
  chunk_size: [
    { value: 'big_picture', label: 'Big Picture' },
    { value: 'detail', label: 'Detail' },
  ],
  action: [
    { value: 'proactive', label: 'Proactive' },
    { value: 'reactive', label: 'Reactive' },
  ],
}

// ============================================================================
// Helpers
// ============================================================================

async function safeFetch<T>(url: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    })
    if (!res.ok) return null
    if (res.status === 204) return null
    return await res.json()
  } catch {
    return null
  }
}

async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

// Dark theme input class
const inputCls = "w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors"
const selectCls = "appearance-none bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors pr-8"
const cardCls = "bg-zinc-800/40 border border-zinc-700/60 rounded-xl p-6 shadow-sm"

/**
 * Map a progress message from the backend to a rough percentage.
 * The backend emits messages at known stages of the ingest pipeline;
 * we translate those into a 0-100 range for the progress bar.
 */
function mapProgressToPercent(msg: string): number {
  const lower = msg.toLowerCase()
  if (lower.includes('source type')) return 5
  if (lower.includes('fetching transcript') || lower.includes('transcribing')) return 15
  if (lower.includes('fetching video metadata')) return 25
  if (lower.includes('transcript ready') || lower.includes('ingesting text')) return 40
  if (lower.includes('extracting training data')) return 50
  if (lower.includes('calling claude')) return 60
  if (lower.includes('extraction complete') || lower.includes('extracted')) return 85
  if (lower.includes('training library updated')) return 95
  return 50
}

// ============================================================================
// Main Component
// ============================================================================

export function MetaEnginePage() {
  // -- Tab state
  const [activeTab, setActiveTab] = useState<TabId>('ingest')

  // -- Ingest tab state
  const [ytUrl, setYtUrl] = useState('')
  const [pasteText, setPasteText] = useState('')
  const [pasteSourceName, setPasteSourceName] = useState('')
  const [ingesting, setIngesting] = useState(false)
  const [ingestResults, setIngestResults] = useState<IngestResult[]>([])
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // -- Library tab state
  const [libraryStats, setLibraryStats] = useState<LibraryStats | null>(null)
  const [examples, setExamples] = useState<TrainingExample[]>([])
  const [patterns, setPatterns] = useState<TrainingPattern[]>([])
  const [coaching, setCoaching] = useState<CoachingScenario[]>([])
  const [libraryFilter, setLibraryFilter] = useState('')
  const [libraryLoading, setLibraryLoading] = useState(false)
  const [libraryView, setLibraryView] = useState<'examples' | 'patterns' | 'coaching'>('examples')

  // -- Writing tab state
  const [writeMotivation, setWriteMotivation] = useState('toward')
  const [writeReference, setWriteReference] = useState('internal')
  const [writeWorkStyle, setWriteWorkStyle] = useState('options')
  const [writeTopic, setWriteTopic] = useState('')
  const [writeChannel, setWriteChannel] = useState(CHANNELS[0])
  const [writeTone, setWriteTone] = useState(TONES[0])
  const [generating, setGenerating] = useState(false)
  const [generatedContent, setGeneratedContent] = useState('')
  const [generateError, setGenerateError] = useState('')
  const [batchGenerating, setBatchGenerating] = useState(false)
  const [batchProgress, setBatchProgress] = useState('')
  const [copied, setCopied] = useState(false)

  // -- Export tab state
  const [outputTopics, setOutputTopics] = useState<OutputTopic[]>([])
  const [exportLoading, setExportLoading] = useState(false)
  const [exportSearch, setExportSearch] = useState('')
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null)

  // -- Settings tab state
  const [settings, setSettings] = useState<MetaEngineSettings>(DEFAULT_SETTINGS)
  const [showApiKey, setShowApiKey] = useState(false)

  // -- Notes tab state
  const [notes, setNotes] = useState<MetaEngineNote[]>([])
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)

  // Load settings and notes from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
      if (raw) setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(raw) })
    } catch { /* ignore corrupt data */ }
    try {
      const raw = localStorage.getItem(NOTES_STORAGE_KEY)
      if (raw) setNotes(JSON.parse(raw))
    } catch { /* ignore corrupt data */ }
  }, [])

  // ========================================================================
  // Settings Handlers
  // ========================================================================

  const updateSetting = useCallback(<K extends keyof MetaEngineSettings>(key: K, value: MetaEngineSettings[K]) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }, [])

  // ========================================================================
  // Notes Handlers
  // ========================================================================

  const persistNotes = useCallback((updated: MetaEngineNote[]) => {
    setNotes(updated)
    localStorage.setItem(NOTES_STORAGE_KEY, JSON.stringify(updated))
  }, [])

  const createNote = useCallback(() => {
    const now = new Date().toISOString()
    const note: MetaEngineNote = {
      id: crypto.randomUUID(),
      label: 'Untitled Note',
      content: '',
      created_at: now,
      updated_at: now,
    }
    const updated = [note, ...notes]
    persistNotes(updated)
    setSelectedNoteId(note.id)
  }, [notes, persistNotes])

  const updateNote = useCallback((id: string, patch: Partial<Pick<MetaEngineNote, 'label' | 'content'>>) => {
    const updated = notes.map(n =>
      n.id === id ? { ...n, ...patch, updated_at: new Date().toISOString() } : n
    )
    persistNotes(updated)
  }, [notes, persistNotes])

  const deleteNote = useCallback((id: string) => {
    const updated = notes.filter(n => n.id !== id)
    persistNotes(updated)
    if (selectedNoteId === id) setSelectedNoteId(null)
  }, [notes, selectedNoteId, persistNotes])

  const selectedNote = notes.find(n => n.id === selectedNoteId) ?? null

  // ========================================================================
  // Ingest Handlers
  // ========================================================================

  const handleIngestUrl = useCallback(async () => {
    if (!ytUrl.trim()) return
    setIngesting(true)
    const result = await safeFetch<IngestResult>('/meta-training/ingest/url', {
      method: 'POST',
      body: JSON.stringify({ url: ytUrl.trim() }),
    })
    setIngestResults(prev => [
      result ?? { source: ytUrl, status: 'error', message: 'Failed to connect to server' },
      ...prev,
    ])
    setYtUrl('')
    setIngesting(false)
  }, [ytUrl])

  const handleIngestText = useCallback(async () => {
    if (!pasteText.trim()) return
    setIngesting(true)
    const result = await safeFetch<IngestResult>('/meta-training/ingest/text', {
      method: 'POST',
      body: JSON.stringify({ text: pasteText.trim(), source_name: pasteSourceName.trim() || 'Pasted text' }),
    })
    setIngestResults(prev => [
      result ?? { source: pasteSourceName || 'Text', status: 'error', message: 'Failed to connect to server' },
      ...prev,
    ])
    setPasteText('')
    setPasteSourceName('')
    setIngesting(false)
  }, [pasteText, pasteSourceName])

  const handleFileDrop = useCallback(async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) return
    await uploadFiles(files)
  }, [])

  const handleFileSelect = useCallback(async (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    if (files.length === 0) return
    await uploadFiles(files)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  async function uploadFiles(files: File[]) {
    setIngesting(true)
    for (const file of files) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const res = await fetch(`${API_BASE}/meta-training/ingest/upload`, {
          method: 'POST',
          body: formData,
        })
        const result: IngestResult = res.ok
          ? await res.json()
          : { source: file.name, status: 'error', message: `Upload failed (HTTP ${res.status})` }
        setIngestResults(prev => [result, ...prev])
      } catch {
        setIngestResults(prev => [
          { source: file.name, status: 'error', message: 'Failed to connect to server' },
          ...prev,
        ])
      }
    }
    setIngesting(false)
  }

  // ========================================================================
  // Library Handlers
  // ========================================================================

  const loadLibrary = useCallback(async () => {
    setLibraryLoading(true)
    const [statsData, exData, patData, coachData] = await Promise.all([
      safeFetch<LibraryStats>('/meta-training/library'),
      safeFetch<TrainingExample[]>(
        `/meta-training/library/examples${libraryFilter ? `?metaprogram=${libraryFilter}` : ''}`
      ),
      safeFetch<TrainingPattern[]>(
        `/meta-training/library/patterns${libraryFilter ? `?metaprogram=${libraryFilter}` : ''}`
      ),
      safeFetch<CoachingScenario[]>('/meta-training/library/coaching'),
    ])
    setLibraryStats(statsData ?? { sources: 0, examples: 0, patterns: 0, scenarios: 0 })
    setExamples(exData ?? [])
    setPatterns(patData ?? [])
    setCoaching(coachData ?? [])
    setLibraryLoading(false)
  }, [libraryFilter])

  // ========================================================================
  // Writing Handlers
  // ========================================================================

  const handleGenerate = useCallback(async () => {
    if (!writeTopic.trim()) return
    setGenerating(true)
    setGenerateError('')
    setGeneratedContent('')
    const result = await safeFetch<{ content: string }>('/meta-training/write/generate', {
      method: 'POST',
      body: JSON.stringify({
        topic: writeTopic.trim(),
        motivation: writeMotivation,
        reference: writeReference,
        work_style: writeWorkStyle,
        channel: writeChannel,
        tone: writeTone,
      }),
    })
    if (result?.content) {
      setGeneratedContent(result.content)
    } else {
      setGenerateError('Generation failed. Check that the server is running and the training library has data.')
    }
    setGenerating(false)
  }, [writeTopic, writeMotivation, writeReference, writeWorkStyle, writeChannel, writeTone])

  const handleGenerateAllCombos = useCallback(async () => {
    if (!writeTopic.trim()) return
    setBatchGenerating(true)
    setBatchProgress('Starting batch generation...')
    const result = await safeFetch<{ generated: number; message: string }>('/meta-training/write/all-combos', {
      method: 'POST',
      body: JSON.stringify({
        topic: writeTopic.trim(),
        channel: writeChannel,
        tone: writeTone,
      }),
    })
    setBatchProgress(result?.message ?? 'Batch generation failed or server unavailable.')
    setBatchGenerating(false)
  }, [writeTopic, writeChannel, writeTone])

  const handleCopy = useCallback(async () => {
    const ok = await copyToClipboard(generatedContent)
    if (ok) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }, [generatedContent])

  // ========================================================================
  // Export Handlers
  // ========================================================================

  const loadOutputTopics = useCallback(async () => {
    setExportLoading(true)
    const data = await safeFetch<OutputTopic[]>('/meta-training/output/topics')
    setOutputTopics(data ?? [])
    setExportLoading(false)
  }, [])

  const handleExport = useCallback(async (slug: string, format: 'csv' | 'json') => {
    try {
      const res = await fetch(`${API_BASE}/meta-training/output/${slug}/export/${format}`)
      if (!res.ok) return
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${slug}.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // Silently fail
    }
  }, [])

  const filteredTopics = exportSearch
    ? outputTopics.filter(t => t.topic.toLowerCase().includes(exportSearch.toLowerCase()))
    : outputTopics

  // ========================================================================
  // Render: Ingest Tab
  // ========================================================================

  function renderIngestTab() {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column: inputs */}
        <div className="space-y-6">
          {/* YouTube URL */}
          <div className={cardCls}>
            <div className="mb-3 flex items-center gap-2">
              <Youtube size={18} className="text-red-500" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-orange-400">YouTube URL</h3>
            </div>
            <div className="flex gap-2">
              <input
                placeholder="https://youtube.com/watch?v=..."
                value={ytUrl}
                onChange={e => setYtUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleIngestUrl()}
                className={inputCls + ' flex-1'}
              />
              <button
                onClick={handleIngestUrl}
                disabled={ingesting || !ytUrl.trim()}
                className="gap-1 bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:opacity-90 transition-opacity border-0 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium flex items-center"
              >
                {ingesting ? <Loader2 size={14} className="animate-spin mr-1" /> : <Send size={14} className="mr-1" />}
                Ingest
              </button>
            </div>
          </div>

          {/* File upload dropzone */}
          <div
            className={`rounded-xl p-8 text-center transition-colors border-2 border-dashed ${
              dragOver
                ? 'border-orange-500 bg-orange-500/10'
                : 'border-zinc-600 bg-zinc-800/20 hover:border-zinc-500'
            }`}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
          >
            <FileAudio size={32} className="mx-auto mb-3 text-zinc-500" />
            <p className="mb-1 text-sm font-semibold text-zinc-300">Drag & drop audio, video, or text files</p>
            <p className="mb-3 text-xs text-zinc-500">MP3, MP4, WAV, TXT, PDF, DOCX</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="border border-zinc-600 text-zinc-300 hover:border-zinc-400 hover:text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              <Upload size={14} className="inline mr-1.5 -mt-0.5" />
              Choose Files
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="audio/*,video/*,.txt,.pdf,.docx,.doc"
              className="hidden"
              onChange={handleFileSelect}
            />
          </div>

          {/* Text paste area */}
          <div className={cardCls}>
            <div className="mb-3 flex items-center gap-2">
              <FileText size={18} className="text-cyan-500" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400">Paste Text</h3>
            </div>
            <input
              placeholder="Source name (optional)"
              value={pasteSourceName}
              onChange={e => setPasteSourceName(e.target.value)}
              className={inputCls + ' mb-2'}
            />
            <textarea
              placeholder="Paste transcript, coaching notes, or training material..."
              value={pasteText}
              onChange={e => setPasteText(e.target.value)}
              rows={5}
              className={inputCls + ' resize-y'}
            />
            <div className="mt-3 flex justify-end">
              <button
                onClick={handleIngestText}
                disabled={ingesting || !pasteText.trim()}
                className="gap-1 bg-gradient-to-r from-cyan-500 to-blue-500 text-white hover:opacity-90 transition-opacity border-0 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium flex items-center"
              >
                {ingesting ? <Loader2 size={14} className="animate-spin mr-1" /> : <Send size={14} className="mr-1" />}
                Ingest Text
              </button>
            </div>
          </div>
        </div>

        {/* Right column: results */}
        <div className={cardCls + ' h-fit'}>
          <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-zinc-400">Ingestion Results</h3>
          {ingestResults.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Layers size={32} className="mb-3 text-zinc-600" />
              <p className="text-sm text-zinc-500">No ingestions yet. Upload content to get started.</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {ingestResults.map((r, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2 rounded-lg border px-3 py-2.5 text-sm ${
                    r.status === 'success'
                      ? 'border-emerald-700/50 bg-emerald-950/30 text-emerald-300'
                      : 'border-red-700/50 bg-red-950/30 text-red-300'
                  }`}
                >
                  {r.status === 'success' ? (
                    <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-emerald-500" />
                  ) : (
                    <XCircle size={14} className="mt-0.5 shrink-0 text-red-500" />
                  )}
                  <div className="min-w-0 flex-1">
                    <span className="font-medium text-white">{r.source}</span>
                    <span className="ml-2 text-zinc-400">{r.message}</span>
                    {r.examples_added != null && (
                      <span className="ml-2 text-xs text-zinc-500">
                        (+{r.examples_added} examples, +{r.patterns_added ?? 0} patterns)
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // ========================================================================
  // Render: Library Tab
  // ========================================================================

  function renderLibraryTab() {
    return (
      <div className="space-y-6">
        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatPill label="Sources" value={libraryStats?.sources ?? 0} color="from-blue-600/20 to-blue-800/10 border-blue-700/40" />
          <StatPill label="Examples" value={libraryStats?.examples ?? 0} color="from-emerald-600/20 to-emerald-800/10 border-emerald-700/40" />
          <StatPill label="Patterns" value={libraryStats?.patterns ?? 0} color="from-amber-600/20 to-amber-800/10 border-amber-700/40" />
          <StatPill label="Scenarios" value={libraryStats?.scenarios ?? 0} color="from-purple-600/20 to-purple-800/10 border-purple-700/40" />
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={loadLibrary}
            disabled={libraryLoading}
            className="gap-1 bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:opacity-90 transition-opacity border-0 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium flex items-center"
          >
            {libraryLoading ? <Loader2 size={14} className="animate-spin mr-1" /> : <RefreshCw size={14} className="mr-1" />}
            Refresh
          </button>

          <div className="flex items-center gap-1.5">
            <Filter size={14} className="text-zinc-500" />
            <select
              value={libraryFilter}
              onChange={e => setLibraryFilter(e.target.value)}
              className={selectCls + ' w-48'}
            >
              {METAPROGRAM_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Sub-view toggle */}
          <div className="ml-auto flex gap-1 rounded-lg border border-zinc-700 bg-zinc-900/50 p-0.5">
            {(['examples', 'patterns', 'coaching'] as const).map(view => (
              <button
                key={view}
                onClick={() => setLibraryView(view)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                  libraryView === view
                    ? 'bg-orange-500/20 text-orange-400 border border-orange-600/40'
                    : 'text-zinc-500 hover:text-zinc-300 border border-transparent'
                }`}
              >
                {view}
              </button>
            ))}
          </div>
        </div>

        {/* Content grid */}
        <div className={cardCls}>
          {libraryLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 size={24} className="animate-spin text-orange-500" />
            </div>
          ) : libraryView === 'examples' ? (
            examples.length === 0 ? (
              <EmptyState icon={<Layers size={32} />} message="No examples yet. Ingest some training material first." />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {examples.map(ex => (
                  <div key={ex.id} className="rounded-lg border border-zinc-700/50 bg-zinc-800/30 p-3">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded">{ex.metaprogram}</span>
                      <span className="text-[10px] font-bold uppercase tracking-wider border border-zinc-600 text-zinc-400 px-2 py-0.5 rounded">{ex.pole}</span>
                      <span className="ml-auto text-[10px] text-zinc-600">{ex.source}</span>
                    </div>
                    <p className="text-sm text-zinc-300 leading-relaxed">{ex.text}</p>
                  </div>
                ))}
              </div>
            )
          ) : libraryView === 'patterns' ? (
            patterns.length === 0 ? (
              <EmptyState icon={<Search size={32} />} message="No patterns detected yet." />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {patterns.map(pat => (
                  <div key={pat.id} className="flex items-center justify-between rounded-lg border border-zinc-700/50 bg-zinc-800/30 p-3">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded mr-2">{pat.metaprogram}</span>
                      <span className="text-sm text-zinc-300">{pat.pattern}</span>
                    </div>
                    <span className="shrink-0 text-xs font-bold text-amber-400 ml-2">{pat.frequency}x</span>
                  </div>
                ))}
              </div>
            )
          ) : (
            coaching.length === 0 ? (
              <EmptyState icon={<Brain size={32} />} message="No coaching scenarios yet." />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {coaching.map(sc => (
                  <div key={sc.id} className="rounded-lg border border-zinc-700/50 bg-zinc-800/30 p-3">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-sm font-semibold text-white">{sc.title}</span>
                      <span className="text-[10px] font-bold uppercase tracking-wider bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded">{sc.metaprogram}</span>
                    </div>
                    <p className="text-sm text-zinc-400 leading-relaxed">{sc.scenario}</p>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </div>
    )
  }

  // ========================================================================
  // Render: Writing Tab
  // ========================================================================

  function renderWritingTab() {
    return (
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Left: Controls */}
        <div className="space-y-6">
          {/* Profile selector */}
          <div className={cardCls}>
            <div className="mb-4 flex items-center gap-2">
              <Sparkles size={18} className="text-amber-500" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-orange-400">Audience Profile</h3>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="space-y-1">
                <span className="text-xs font-medium text-zinc-500">Motivation</span>
                <select value={writeMotivation} onChange={e => setWriteMotivation(e.target.value)} className={selectCls + ' w-full'}>
                  {POLE_OPTIONS.motivation.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </label>
              <label className="space-y-1">
                <span className="text-xs font-medium text-zinc-500">Reference</span>
                <select value={writeReference} onChange={e => setWriteReference(e.target.value)} className={selectCls + ' w-full'}>
                  {POLE_OPTIONS.reference.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </label>
              <label className="space-y-1">
                <span className="text-xs font-medium text-zinc-500">Work Style</span>
                <select value={writeWorkStyle} onChange={e => setWriteWorkStyle(e.target.value)} className={selectCls + ' w-full'}>
                  {POLE_OPTIONS.work_style.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </label>
            </div>
          </div>

          {/* Topic, channel, tone */}
          <div className={cardCls}>
            <div className="mb-4 flex items-center gap-2">
              <PenTool size={18} className="text-violet-500" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400">Content Setup</h3>
            </div>
            <div className="space-y-3">
              <input
                placeholder="Topic (e.g., 'Benefits of morning routines')"
                value={writeTopic}
                onChange={e => setWriteTopic(e.target.value)}
                className={inputCls}
              />
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="space-y-1">
                  <span className="text-xs font-medium text-zinc-500">Channel</span>
                  <select value={writeChannel} onChange={e => setWriteChannel(e.target.value)} className={selectCls + ' w-full'}>
                    {CHANNELS.map(ch => <option key={ch} value={ch}>{ch}</option>)}
                  </select>
                </label>
                <label className="space-y-1">
                  <span className="text-xs font-medium text-zinc-500">Tone</span>
                  <select value={writeTone} onChange={e => setWriteTone(e.target.value)} className={selectCls + ' w-full'}>
                    {TONES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </label>
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  onClick={handleGenerate}
                  disabled={generating || !writeTopic.trim()}
                  className="gap-1 bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:opacity-90 transition-opacity border-0 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium flex items-center"
                >
                  {generating ? <Loader2 size={14} className="animate-spin mr-1" /> : <Send size={14} className="mr-1" />}
                  Generate
                </button>
                <button
                  onClick={handleGenerateAllCombos}
                  disabled={batchGenerating || !writeTopic.trim()}
                  className="border border-zinc-600 text-zinc-300 hover:border-orange-500 hover:text-orange-400 px-4 py-2 rounded-lg text-sm font-medium flex items-center transition-colors disabled:opacity-40"
                >
                  {batchGenerating ? <Loader2 size={14} className="animate-spin mr-1" /> : <Layers size={14} className="mr-1" />}
                  Generate All Combos
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Output */}
        <div className={cardCls + ' h-fit'}>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-400">Generated Output</h3>
            {generatedContent && (
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition-colors"
              >
                {copied ? <CheckCircle2 size={14} className="text-emerald-500" /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            )}
          </div>
          {generateError && (
            <p className="text-sm text-red-400 mb-3">{generateError}</p>
          )}
          {generatedContent ? (
            <div className="whitespace-pre-wrap rounded-lg border border-zinc-700/50 bg-zinc-900 p-4 text-sm leading-relaxed text-zinc-300 max-h-[500px] overflow-y-auto">
              {generatedContent}
            </div>
          ) : (
            <EmptyState icon={<PenTool size={32} />} message="Configure a profile and topic, then click Generate." />
          )}
          {batchProgress && (
            <p className="mt-3 text-sm text-amber-400">{batchProgress}</p>
          )}
        </div>
      </div>
    )
  }

  // ========================================================================
  // Render: Export Tab
  // ========================================================================

  function renderExportTab() {
    return (
      <div className="space-y-6">
        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={loadOutputTopics}
            disabled={exportLoading}
            className="gap-1 bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:opacity-90 transition-opacity border-0 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium flex items-center"
          >
            {exportLoading ? <Loader2 size={14} className="animate-spin mr-1" /> : <RefreshCw size={14} className="mr-1" />}
            Refresh
          </button>
          <div className="relative flex-1 sm:max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              placeholder="Search topics..."
              value={exportSearch}
              onChange={e => setExportSearch(e.target.value)}
              className={inputCls + ' pl-9'}
            />
          </div>
        </div>

        {/* Topic list */}
        {exportLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-orange-500" />
          </div>
        ) : filteredTopics.length === 0 ? (
          <div className={cardCls}>
            <EmptyState icon={<Download size={32} />} message="No generated output yet. Use the Writing Engine to generate content first." />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredTopics.map(topic => (
              <div key={topic.slug} className={cardCls}>
                {/* Topic header */}
                <button
                  onClick={() => setExpandedTopic(expandedTopic === topic.slug ? null : topic.slug)}
                  className="flex w-full items-center justify-between text-left"
                >
                  <div className="flex items-center gap-3">
                    <FileText size={16} className="text-zinc-500" />
                    <span className="text-sm font-semibold text-white">{topic.topic}</span>
                    <span className="text-[10px] font-bold bg-zinc-700/50 text-zinc-400 px-2 py-0.5 rounded">
                      {topic.output_count} variant{topic.output_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={e => { e.stopPropagation(); handleExport(topic.slug, 'csv') }}
                      className="text-xs text-zinc-500 hover:text-orange-400 transition-colors"
                    >CSV</button>
                    <button
                      onClick={e => { e.stopPropagation(); handleExport(topic.slug, 'json') }}
                      className="text-xs text-zinc-500 hover:text-cyan-400 transition-colors"
                    >JSON</button>
                  </div>
                </button>

                {/* Expanded outputs */}
                {expandedTopic === topic.slug && topic.outputs.length > 0 && (
                  <div className="border-t border-zinc-700/40 mt-4 pt-4 space-y-3">
                    {topic.outputs.map((out, i) => (
                      <div key={i} className="rounded-lg border border-zinc-700/30 bg-zinc-900/50 p-3">
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                          <span className="text-[10px] font-bold bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded">{out.profile}</span>
                          <span className="text-[10px] font-bold bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded">{out.channel}</span>
                          <span className="text-[10px] font-bold bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded">{out.tone}</span>
                          <span className="ml-auto text-[10px] text-zinc-600">{out.created_at}</span>
                        </div>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300">{out.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ========================================================================
  // Render: Settings Tab
  // ========================================================================

  function renderSettingsTab() {
    return (
      <div className="max-w-2xl space-y-6">
        {/* Workspace folder */}
        <div className={cardCls}>
          <div className="mb-4 flex items-center gap-2">
            <FolderOpen size={18} className="text-amber-500" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-orange-400">Workspace Folder</h3>
          </div>
          <p className="text-xs text-zinc-500 mb-3">
            Where training data, notes, and exports get saved.
          </p>
          <div className="flex gap-2">
            <input
              placeholder="/path/to/metaengine-workspace"
              value={settings.workspaceFolder}
              onChange={e => updateSetting('workspaceFolder', e.target.value)}
              className={inputCls + ' flex-1'}
            />
            <button
              onClick={() => {
                // Browser cannot open native folder picker without a file input.
                // Use a hidden directory input as a best-effort approach.
                const input = document.createElement('input')
                input.type = 'file'
                // webkitdirectory is widely supported but not standard
                input.setAttribute('webkitdirectory', '')
                input.onchange = () => {
                  const files = Array.from(input.files ?? [])
                  if (files.length > 0) {
                    // Extract directory path from the first file's webkitRelativePath
                    const rel = files[0].webkitRelativePath
                    const folder = rel.split('/')[0]
                    if (folder) updateSetting('workspaceFolder', folder)
                  }
                }
                input.click()
              }}
              className="border border-zinc-600 text-zinc-300 hover:border-orange-500 hover:text-orange-400 px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-1.5"
            >
              <FolderOpen size={14} />
              Browse
            </button>
          </div>
        </div>

        {/* OpenAI API key */}
        <div className={cardCls}>
          <div className="mb-4 flex items-center gap-2">
            <Sparkles size={18} className="text-cyan-500" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-400">OpenAI API Key</h3>
          </div>
          <p className="text-xs text-zinc-500 mb-3">
            Used for Whisper transcription of uploaded audio/video.
          </p>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              placeholder="sk-..."
              value={settings.openaiApiKey}
              onChange={e => updateSetting('openaiApiKey', e.target.value)}
              className={inputCls + ' pr-10'}
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        {/* Defaults */}
        <div className={cardCls}>
          <div className="mb-4 flex items-center gap-2">
            <Settings size={18} className="text-violet-500" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-violet-400">Defaults</h3>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-1">
              <span className="text-xs font-medium text-zinc-500">Default Channel</span>
              <select
                value={settings.defaultChannel}
                onChange={e => updateSetting('defaultChannel', e.target.value)}
                className={selectCls + ' w-full'}
              >
                {CHANNELS.map(ch => <option key={ch} value={ch}>{ch}</option>)}
              </select>
            </label>
            <label className="space-y-1">
              <span className="text-xs font-medium text-zinc-500">Default Tone</span>
              <select
                value={settings.defaultTone}
                onChange={e => updateSetting('defaultTone', e.target.value)}
                className={selectCls + ' w-full'}
              >
                {TONES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </label>
          </div>
        </div>

        {/* Auto-ingest toggle */}
        <div className={cardCls}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Auto-Ingest</h3>
              <p className="text-xs text-zinc-500 mt-0.5">Automatically ingest new files dropped into the workspace folder.</p>
            </div>
            <button
              onClick={() => updateSetting('autoIngest', !settings.autoIngest)}
              className={`relative w-12 h-7 rounded-full transition-colors ${
                settings.autoIngest ? 'bg-orange-500' : 'bg-zinc-700'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white shadow transition-transform ${
                  settings.autoIngest ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Saved indicator */}
        <div className="flex items-center gap-2 text-xs text-zinc-600">
          <Save size={12} />
          <span>Settings are saved automatically to localStorage.</span>
        </div>
      </div>
    )
  }

  // ========================================================================
  // Render: Notes Tab
  // ========================================================================

  function renderNotesTab() {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6 min-h-[500px]">
        {/* Left sidebar: notes list */}
        <div className={cardCls + ' flex flex-col overflow-hidden'}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-orange-400">Notes</h3>
            <button
              onClick={createNote}
              className="gap-1 bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:opacity-90 transition-opacity border-0 px-3 py-1.5 rounded-lg text-xs font-medium flex items-center"
            >
              <Plus size={12} />
              New Note
            </button>
          </div>
          {notes.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
              <StickyNote size={28} className="mb-2 text-zinc-600" />
              <p className="text-xs text-zinc-500">No notes yet. Create one to get started.</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto space-y-1 -mx-2 px-2">
              {notes.map(note => (
                <div
                  key={note.id}
                  onClick={() => setSelectedNoteId(note.id)}
                  className={`group flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer transition-colors ${
                    selectedNoteId === note.id
                      ? 'bg-zinc-700/50 border border-orange-600/40'
                      : 'hover:bg-zinc-800/60 border border-transparent'
                  }`}
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: labelColor(note.label) }}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-zinc-200 truncate">{note.label}</p>
                    <p className="text-[10px] text-zinc-600">
                      {new Date(note.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </p>
                  </div>
                  <button
                    onClick={e => { e.stopPropagation(); deleteNote(note.id) }}
                    className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition-all p-0.5"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right side: editor */}
        <div className={cardCls + ' flex flex-col'}>
          {selectedNote ? (
            <>
              <div className="mb-4 flex items-center gap-3">
                <span
                  className="w-3 h-3 rounded-full shrink-0"
                  style={{ backgroundColor: labelColor(selectedNote.label) }}
                />
                <input
                  value={selectedNote.label}
                  onChange={e => updateNote(selectedNote.id, { label: e.target.value })}
                  className="bg-transparent text-lg font-bold text-white border-none outline-none flex-1 placeholder-zinc-600"
                  placeholder="Note title..."
                />
                <span className="text-[10px] text-zinc-600 shrink-0">
                  {new Date(selectedNote.updated_at).toLocaleString()}
                </span>
              </div>
              <textarea
                value={selectedNote.content}
                onChange={e => updateNote(selectedNote.id, { content: e.target.value })}
                placeholder="Start writing..."
                className="flex-1 min-h-[350px] bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-sm text-zinc-300 leading-relaxed resize-y focus:border-orange-500 focus:outline-none transition-colors"
              />
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center">
              <StickyNote size={40} className="mb-3 text-zinc-700" />
              <p className="text-sm text-zinc-500">Select a note or create a new one.</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ========================================================================
  // Main Render
  // ========================================================================

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-zinc-800/60">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-zinc-400 hover:text-white"
              onClick={() => { window.location.hash = '' }}
            >
              <ArrowLeft size={16} />
              <span className="text-xs">Home</span>
            </Button>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-400 via-amber-300 to-yellow-400 bg-clip-text text-transparent">
                Metaprogram Engine
              </h1>
              <p className="text-xs text-zinc-500 mt-0.5">
                Ingest training material, build a pattern library, generate audience-adapted copy
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Tab navigation */}
      <div className="border-b border-zinc-800/60 px-6">
        <div className="flex gap-1">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab.id
                  ? 'border-orange-500 text-orange-400'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300 hover:border-zinc-700'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <main className="px-6 py-6">
        {activeTab === 'ingest' && renderIngestTab()}
        {activeTab === 'library' && renderLibraryTab()}
        {activeTab === 'writing' && renderWritingTab()}
        {activeTab === 'export' && renderExportTab()}
        {activeTab === 'notes' && renderNotesTab()}
        {activeTab === 'settings' && renderSettingsTab()}
      </main>
    </div>
  )
}

// ============================================================================
// Shared sub-components
// ============================================================================

function StatPill({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`flex flex-col items-center justify-center rounded-xl border bg-gradient-to-br px-5 py-4 ${color}`}>
      <span className="text-3xl font-black text-white">{value}</span>
      <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">{label}</span>
    </div>
  )
}

function EmptyState({ icon, message }: { icon: React.ReactNode; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-3 text-zinc-600">{icon}</div>
      <p className="text-sm text-zinc-500">{message}</p>
    </div>
  )
}
