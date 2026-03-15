import { useState, useRef, useEffect } from 'react'
import { ArrowLeft, Upload, RotateCcw, Trash2, ChevronRight, FileText, Loader2, CheckCircle2, XCircle, Clock, Zap, AlertTriangle, Moon, Sun, Flame, GitCommit, TestTube, Search, Code2, Play, Activity, History, ListOrdered, Terminal, Settings } from 'lucide-react'
import type { ShredderQueueItem } from '@/lib/api'
import {
  useShredderQueue,
  useShredderStats,
  useShredderStatus,
  useShredderItemLogs,
  useEnqueuePRD,
  useRetryItem,
  useRetryAllFailed,
  useDeleteItem,
} from '@/hooks/usePRDShredder'
import { useTheme } from '@/hooks/useTheme'
import { BuildRulesPanel } from '@/components/prd-shredder/BuildRulesPanel'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const ACTIVE_STATUSES = ['cloning', 'analyzing', 'building', 'testing', 'committing', 'qa_testing']

function relativeTime(isoStr: string | null): string {
  if (!isoStr) return '—'
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function formatDateTime(isoStr: string | null): { date: string; time: string } {
  if (!isoStr) return { date: '—', time: '' }
  const d = new Date(isoStr)
  return {
    date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    time: d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
  }
}

// ---------------------------------------------------------------------------
// Status config — vibrant badge colors
// ---------------------------------------------------------------------------
const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  queued:     { label: 'Queued',      color: 'bg-amber-500/20 text-amber-400 border-amber-500/40',    icon: <Clock size={12} /> },
  cloning:    { label: 'Cloning',     color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40',       icon: <Loader2 size={12} className="animate-spin" /> },
  analyzing:  { label: 'Analyzing',   color: 'bg-blue-500/20 text-blue-400 border-blue-500/40',       icon: <Search size={12} className="animate-pulse" /> },
  building:   { label: 'Building',    color: 'bg-orange-500/20 text-orange-400 border-orange-500/40', icon: <Code2 size={12} className="animate-spin" /> },
  testing:    { label: 'Testing',     color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40', icon: <TestTube size={12} className="animate-spin" /> },
  committing: { label: 'Committing',  color: 'bg-teal-500/20 text-teal-400 border-teal-500/40',       icon: <GitCommit size={12} className="animate-spin" /> },
  qa_testing: { label: 'QA Testing',  color: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/40', icon: <Play size={12} className="animate-spin" /> },
  done:       { label: 'Done',        color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40', icon: <CheckCircle2 size={12} /> },
  failed:     { label: 'Failed',      color: 'bg-red-500/20 text-red-400 border-red-500/40',          icon: <XCircle size={12} /> },
}

const STATUS_ACCENT: Record<string, string> = {
  queued: 'border-l-amber-500', cloning: 'border-l-cyan-500', analyzing: 'border-l-blue-500',
  building: 'border-l-orange-500', testing: 'border-l-yellow-500', committing: 'border-l-teal-500',
  qa_testing: 'border-l-indigo-500', done: 'border-l-emerald-500', failed: 'border-l-red-500',
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || { label: status, color: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30', icon: null }
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-semibold rounded border ${cfg.color}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Stats pills — header bar
// ---------------------------------------------------------------------------
function StatsBar({ stats }: { stats: { total: number; queued: number; building: number; done: number; failed: number } }) {
  return (
    <div className="flex items-center gap-2">
      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-200 dark:bg-zinc-700/50 text-zinc-500 dark:text-zinc-400 border border-zinc-300 dark:border-zinc-600/50">
        {stats.total} total
      </span>
      {stats.queued > 0 && (
        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30">
          {stats.queued} queued
        </span>
      )}
      {stats.building > 0 && (
        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-orange-500/15 text-orange-400 border border-orange-500/30 animate-pulse">
          {stats.building} building
        </span>
      )}
      {stats.done > 0 && (
        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          {stats.done} done
        </span>
      )}
      {stats.failed > 0 && (
        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-red-500/15 text-red-400 border border-red-500/30">
          {stats.failed} failed
        </span>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Section card — matte dark card like CLI Scripter
// ---------------------------------------------------------------------------
function SectionCard({ icon, title, count, accent, children }: {
  icon: React.ReactNode
  title: string
  count?: number
  accent?: string // border color accent
  children: React.ReactNode
}) {
  return (
    <div className={`bg-zinc-100 dark:bg-zinc-800/40 border rounded-xl p-5 shadow-sm ${accent || 'border-zinc-200 dark:border-zinc-700/60'}`}>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h2 className="text-sm font-bold text-zinc-900 dark:text-white uppercase tracking-wider">{title}</h2>
        {count !== undefined && count > 0 && (
          <span className="text-[10px] font-bold text-zinc-500 bg-zinc-200 dark:bg-zinc-700/50 rounded px-1.5 py-0.5">{count}</span>
        )}
      </div>
      {children}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Live log viewer — terminal style
// ---------------------------------------------------------------------------
function LiveLogViewer({ itemId }: { itemId: string }) {
  const { data } = useShredderItemLogs(itemId)
  const containerRef = useRef<HTMLDivElement>(null)
  const logs = data?.logs || []

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [logs.length])

  return (
    <div
      ref={containerRef}
      className="bg-zinc-900 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg p-3 max-h-72 overflow-y-auto font-mono text-[11px] leading-relaxed"
    >
      {logs.length === 0 ? (
        <div className="flex items-center gap-2 text-zinc-600 italic">
          <Loader2 size={12} className="animate-spin text-orange-500" />
          Waiting for logs...
        </div>
      ) : (
        logs.map((line, i) => (
          <div key={i} className="text-zinc-500 hover:text-zinc-300 transition-colors py-px">
            <span className="text-zinc-700 select-none mr-2 text-[10px]">{String(i + 1).padStart(3)}</span>
            {line}
          </div>
        ))
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Active Build Card — color adapts to current status
// ---------------------------------------------------------------------------
const STATUS_THEME: Record<string, { gradient: string; shadow: string; text: string; shimmer: string; dots: [string, string, string] }> = {
  cloning:    { gradient: 'from-cyan-500 to-teal-500',     shadow: 'shadow-cyan-500/20',    text: 'text-cyan-400',    shimmer: 'from-cyan-500 via-teal-400 to-cyan-500',       dots: ['bg-cyan-500', 'bg-teal-400', 'bg-emerald-400'] },
  analyzing:  { gradient: 'from-blue-500 to-indigo-500',   shadow: 'shadow-blue-500/20',    text: 'text-blue-400',    shimmer: 'from-blue-500 via-indigo-400 to-blue-500',     dots: ['bg-blue-500', 'bg-indigo-400', 'bg-violet-400'] },
  building:   { gradient: 'from-orange-500 to-amber-500',  shadow: 'shadow-orange-500/20',  text: 'text-orange-400',  shimmer: 'from-orange-500 via-amber-400 to-orange-500',  dots: ['bg-orange-500', 'bg-amber-400', 'bg-yellow-400'] },
  testing:    { gradient: 'from-yellow-500 to-lime-500',   shadow: 'shadow-yellow-500/20',  text: 'text-yellow-400',  shimmer: 'from-yellow-500 via-lime-400 to-yellow-500',   dots: ['bg-yellow-500', 'bg-lime-400', 'bg-green-400'] },
  committing: { gradient: 'from-teal-500 to-emerald-500',  shadow: 'shadow-teal-500/20',    text: 'text-teal-400',    shimmer: 'from-teal-500 via-emerald-400 to-teal-500',    dots: ['bg-teal-500', 'bg-emerald-400', 'bg-green-400'] },
  qa_testing: { gradient: 'from-violet-500 to-purple-500', shadow: 'shadow-violet-500/20',  text: 'text-violet-400',  shimmer: 'from-violet-500 via-purple-400 to-violet-500', dots: ['bg-violet-500', 'bg-purple-400', 'bg-fuchsia-400'] },
}

function ActiveBuildCard({ item }: { item: ShredderQueueItem }) {
  const progress = item.tasks_total > 0 ? Math.round((item.tasks_done / item.tasks_total) * 100) : 0
  const theme = STATUS_THEME[item.status] || STATUS_THEME.building

  return (
    <div className="bg-zinc-100 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-700/60 rounded-xl overflow-hidden">
      {/* Animated top bar — color matches status */}
      <div className={`h-1 bg-gradient-to-r ${theme.shimmer} bg-[length:200%_100%] animate-[shimmer_2s_linear_infinite]`} />

      <div className="p-5 space-y-4">
        {/* Header row */}
        <div className="flex items-center gap-3">
          {/* Pulsing orb — color matches status */}
          <div className="relative">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${theme.gradient} flex items-center justify-center shadow-lg ${theme.shadow}`}>
              <Code2 size={18} className="text-white animate-spin" style={{ animationDuration: '3s' }} />
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-white dark:border-zinc-800 animate-pulse" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-zinc-900 dark:text-white truncate">{item.title}</span>
              <StatusBadge status={item.status} />
            </div>
            <div className="flex items-center gap-3 mt-0.5">
              <span className="text-[11px] text-zinc-500 dark:text-zinc-500 font-mono truncate">
                {item.target_repo.split('/').pop() || item.target_repo}
              </span>
              {item.tasks_total > 0 && (
                <span className="text-[11px] text-zinc-500 dark:text-zinc-500">
                  {item.tasks_done}/{item.tasks_total} tasks
                </span>
              )}
            </div>
          </div>

          {/* Progress */}
          {item.tasks_total > 0 && (
            <div className={`text-lg font-bold ${theme.text}`}>{progress}%</div>
          )}
        </div>

        {/* Pipeline stage indicators */}
        <div className="flex items-center gap-1">
          {(['cloning', 'analyzing', 'building', 'testing', 'committing', 'qa_testing'] as const).map((stage) => {
            const stageIdx = ACTIVE_STATUSES.indexOf(stage)
            const currentIdx = ACTIVE_STATUSES.indexOf(item.status)
            const isDone = stageIdx < currentIdx
            const isCurrent = stage === item.status
            const cfg = STATUS_CONFIG[stage]
            return (
              <div key={stage} className="flex items-center gap-1">
                <div className={`px-1.5 py-0.5 rounded text-[9px] font-bold border transition-all ${
                  isCurrent ? cfg.color + ' animate-pulse' :
                  isDone ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
                  'bg-zinc-200/60 dark:bg-zinc-800/60 text-zinc-400 dark:text-zinc-600 border-zinc-300/40 dark:border-zinc-700/40'
                }`}>
                  {cfg.label.slice(0, 3).toUpperCase()}
                </div>
                {stage !== 'qa_testing' && (
                  <ChevronRight size={10} className={isDone ? 'text-emerald-500/50' : 'text-zinc-700'} />
                )}
              </div>
            )
          })}
        </div>

        {/* Progress bar — color matches status */}
        {item.tasks_total > 0 && (
          <div className="h-1.5 bg-zinc-200 dark:bg-zinc-900 rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${theme.shimmer} bg-[length:200%_100%] rounded-full transition-all duration-700 animate-[shimmer_2s_linear_infinite]`}
              style={{ width: `${Math.max(progress, 5)}%` }}
            />
          </div>
        )}

        {/* Error display */}
        {item.error && (
          <div className="flex items-start gap-2.5 p-2.5 bg-red-500/10 border border-red-500/25 rounded-lg text-xs text-red-400">
            <AlertTriangle size={14} className="shrink-0 mt-0.5 text-red-500" />
            <span className="line-clamp-2">{item.error}</span>
          </div>
        )}

        {/* Log header with bouncing dots — colors match status */}
        <div className="flex items-center gap-2 text-[11px] text-zinc-500 dark:text-zinc-500">
          <Terminal size={12} className={theme.text} />
          <span className="font-medium text-zinc-600 dark:text-zinc-400">Live Build Output</span>
          <div className="flex gap-0.5 ml-1">
            <span className={`w-1 h-1 rounded-full ${theme.dots[0]} animate-bounce`} style={{ animationDelay: '0ms' }} />
            <span className={`w-1 h-1 rounded-full ${theme.dots[1]} animate-bounce`} style={{ animationDelay: '150ms' }} />
            <span className={`w-1 h-1 rounded-full ${theme.dots[2]} animate-bounce`} style={{ animationDelay: '300ms' }} />
          </div>
        </div>

        {/* Live logs */}
        <LiveLogViewer itemId={item.id} />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Queue row — compact, for waiting items
// ---------------------------------------------------------------------------
function QueueRow({ item, position, onDelete }: { item: ShredderQueueItem; position: number; onDelete: (id: string) => void }) {
  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-700/40 hover:border-zinc-300 dark:hover:border-zinc-600/60 transition-colors group">
      {/* Position */}
      <div className="w-6 h-6 rounded bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
        <span className="text-[10px] font-bold text-amber-500 dark:text-amber-400">{position}</span>
      </div>

      <div className="flex-1 min-w-0">
        <span className="text-xs font-medium text-zinc-900 dark:text-white truncate block">{item.title}</span>
        <span className="text-[10px] text-zinc-500 dark:text-zinc-600 font-mono truncate block">
          {item.target_repo.split('/').pop() || item.target_repo}
        </span>
      </div>

      <StatusBadge status={item.status} />
      <span className="text-[10px] text-zinc-600">{relativeTime(item.created_at)}</span>

      <button
        className="h-6 w-6 flex items-center justify-center rounded text-zinc-600 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
        onClick={() => onDelete(item.id)}
        title="Remove"
      >
        <Trash2 size={11} />
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// History row — completed/failed with timestamps
// ---------------------------------------------------------------------------
function HistoryRow({ item, onRetry, onDelete }: {
  item: ShredderQueueItem
  onRetry: (id: string) => void
  onDelete: (id: string) => void
}) {
  const { date, time } = formatDateTime(item.completed_at || item.created_at)
  const accent = STATUS_ACCENT[item.status] || 'border-l-zinc-600'
  const isDone = item.status === 'done'
  const [showLogs, setShowLogs] = useState(false)

  return (
    <div className={`bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-700/40 border-l-4 ${accent} rounded-lg hover:border-zinc-300 dark:hover:border-zinc-600/60 transition-colors group`}>
      <div className="flex items-center gap-3 px-3 py-2.5">
        {/* Status icon */}
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${isDone ? 'bg-emerald-500/15 border border-emerald-500/30' : 'bg-red-500/15 border border-red-500/30'}`}>
          {isDone
            ? <CheckCircle2 size={14} className="text-emerald-400" />
            : <XCircle size={14} className="text-red-400" />
          }
        </div>

        <div className="flex-1 min-w-0">
          <span className="text-xs font-medium text-zinc-900 dark:text-white truncate block">{item.title}</span>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-[10px] text-zinc-500 dark:text-zinc-600 font-mono truncate">
              {item.target_repo.split('/').pop() || item.target_repo}
            </span>
            {item.commit_hash && (
              <span className="text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-1.5 py-px rounded border border-emerald-500/20">
                {item.commit_hash}
              </span>
            )}
            {item.tasks_total > 0 && (
              <span className="text-[10px] text-zinc-600">
                {item.tasks_done}/{item.tasks_total}
              </span>
            )}
          </div>
        </div>

        {/* Timestamp */}
        <div className="text-right shrink-0">
          <div className="text-[11px] font-medium text-zinc-600 dark:text-zinc-400">{date}</div>
          <div className="text-[10px] text-zinc-400 dark:text-zinc-600">{time}</div>
        </div>

        <StatusBadge status={item.status} />

        {/* Actions — show on hover */}
        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          {item.status === 'failed' && (
            <button className="h-6 w-6 flex items-center justify-center rounded text-amber-500 hover:bg-amber-500/10 transition-colors" onClick={() => onRetry(item.id)} title="Retry">
              <RotateCcw size={11} />
            </button>
          )}
          <button className="h-6 w-6 flex items-center justify-center rounded text-zinc-600 hover:text-zinc-300 transition-colors" onClick={() => setShowLogs(v => !v)} title="View logs">
            <Terminal size={11} />
          </button>
          <button className="h-6 w-6 flex items-center justify-center rounded text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-colors" onClick={() => onDelete(item.id)} title="Delete">
            <Trash2 size={11} />
          </button>
        </div>
      </div>

      {/* Expandable error + logs */}
      {showLogs && (
        <div className="px-3 pb-3 space-y-2 border-t border-zinc-200 dark:border-zinc-800/60 mt-1 pt-2">
          {item.error && (
            <div className="flex items-start gap-2 p-2 bg-red-500/10 border border-red-500/25 rounded text-[11px] text-red-400">
              <AlertTriangle size={12} className="shrink-0 mt-0.5 text-red-500" />
              <span>{item.error}</span>
            </div>
          )}
          {item.playwright_errors.length > 0 && (
            <div className="flex items-start gap-2 p-2 bg-orange-500/10 border border-orange-500/25 rounded text-[11px] text-orange-400">
              <TestTube size={12} className="shrink-0 mt-0.5 text-orange-500" />
              <span className="font-medium">Playwright found {item.playwright_errors.length} error(s)</span>
            </div>
          )}
          <LiveLogViewer itemId={item.id} />
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Enqueue form — cyan/teal accents (distinct from orange header)
// ---------------------------------------------------------------------------
function EnqueueForm({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('')
  const [prdText, setPrdText] = useState('')
  const [targetRepo, setTargetRepo] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const enqueue = useEnqueuePRD()

  function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const text = reader.result as string
      setPrdText(text)
      if (!title) {
        const firstLine = text.split('\n')[0].replace(/^#+\s*/, '').trim()
        setTitle(firstLine || file.name.replace('.md', ''))
      }
    }
    reader.readAsText(file)
  }

  function handleSubmit() {
    if (!title.trim() || !prdText.trim() || !targetRepo.trim()) return
    enqueue.mutate(
      { title: title.trim(), prd_text: prdText, target_repo: targetRepo.trim() },
      { onSuccess: () => onClose() },
    )
  }

  return (
    <div className="bg-zinc-100 dark:bg-zinc-800/40 border border-cyan-300/40 dark:border-cyan-700/40 rounded-xl p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-cyan-600 dark:text-cyan-400 flex items-center gap-2">
          <Flame size={16} className="text-cyan-500" />
          Drop a PRD
        </h3>
        <button className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors" onClick={onClose}>Cancel</button>
      </div>

      <input
        type="text"
        placeholder="PRD title"
        value={title}
        onChange={e => setTitle(e.target.value)}
        className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-3 py-2 text-zinc-900 dark:text-white text-sm placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:border-cyan-500 focus:outline-none transition-colors"
      />

      <input
        type="text"
        placeholder="Target repo path (e.g. C:\Users\lober\GitHub\...)"
        value={targetRepo}
        onChange={e => setTargetRepo(e.target.value)}
        className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-3 py-2 text-zinc-900 dark:text-white text-sm placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:border-cyan-500 focus:outline-none transition-colors"
      />

      <div className="flex items-center gap-3">
        <button
          className="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400 hover:text-cyan-500 dark:hover:text-cyan-400 transition-colors px-2 py-1 rounded border border-zinc-300 dark:border-zinc-700 hover:border-cyan-500/50"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={13} />
          Upload .md file
        </button>
        <input ref={fileInputRef} type="file" accept=".md,.txt" className="hidden" onChange={handleFileUpload} />
        {prdText && (
          <span className="text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
            {prdText.length.toLocaleString()} chars loaded
          </span>
        )}
      </div>

      {!prdText && (
        <textarea
          placeholder="Or paste PRD text here..."
          value={prdText}
          onChange={e => setPrdText(e.target.value)}
          rows={6}
          className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-lg px-3 py-2 text-xs font-mono text-zinc-700 dark:text-zinc-300 placeholder:text-zinc-400 dark:placeholder:text-zinc-600 resize-y focus:border-cyan-500 focus:outline-none transition-colors"
        />
      )}

      <div className="flex justify-end">
        <button
          className="flex items-center gap-2 text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg px-4 py-2 hover:opacity-90 transition-opacity disabled:opacity-40 shadow-lg shadow-emerald-500/20"
          onClick={handleSubmit}
          disabled={!title.trim() || !prdText.trim() || !targetRepo.trim() || enqueue.isPending}
        >
          {enqueue.isPending ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
          Shred It
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export function PRDShredderPage() {
  const { darkMode, setDarkMode, toggleDarkMode } = useTheme()

  useEffect(() => {
    if (!darkMode) {
      const stored = localStorage.getItem('autoforge-dark-mode')
      if (stored === null) setDarkMode(true)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const [showForm, setShowForm] = useState(false)
  const [rulesOpen, setRulesOpen] = useState(false)

  const { data: queueData } = useShredderQueue()
  const { data: stats } = useShredderStats()
  const { data: status } = useShredderStatus()
  const retryItem = useRetryItem()
  const retryAll = useRetryAllFailed()
  const deleteItem = useDeleteItem()

  const allItems = queueData?.items || []
  const failedCount = stats?.failed || 0

  // Split into 3 buckets
  const activeItems = allItems.filter(i => ACTIVE_STATUSES.includes(i.status))
  const queuedItems = allItems.filter(i => i.status === 'queued')
  const historyItems = allItems.filter(i => i.status === 'done' || i.status === 'failed')

  const hasContent = allItems.length > 0

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-[#0a0a0a] text-zinc-900 dark:text-white">
      {/* Header — sticky like CLI Scripter */}
      <header className="sticky top-0 z-50 bg-white/90 dark:bg-[#0a0a0a]/90 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800/60">
        {/* Orange/amber gradient top line */}
        <div className="h-0.5 bg-gradient-to-r from-orange-500 via-amber-400 to-yellow-500" />
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => { window.location.hash = '' }}
              className="text-zinc-400 hover:text-white transition-colors"
              title="Back to AutoForge"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-orange-400 via-amber-300 to-yellow-400 bg-clip-text text-transparent">
                PRD Shredder
              </h1>
              <div className="flex items-center gap-2 mt-0.5">
                <span
                  className={`w-2 h-2 rounded-full ${status?.running ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50 animate-pulse' : 'bg-red-400 shadow-lg shadow-red-400/30'}`}
                />
                <span className="text-[10px] text-zinc-500">{status?.running ? 'Engine running' : 'Engine stopped'}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {stats && <StatsBar stats={stats} />}

            {failedCount > 0 && (
              <button
                className="flex items-center gap-1 text-[11px] text-amber-400 border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 rounded px-2 py-1 transition-colors disabled:opacity-40"
                onClick={() => retryAll.mutate()}
                disabled={retryAll.isPending}
              >
                <RotateCcw size={11} />
                Retry {failedCount}
              </button>
            )}

            <button
              className="flex items-center gap-1.5 text-[11px] font-semibold bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-lg px-3 py-1.5 hover:opacity-90 transition-opacity shadow-md shadow-orange-500/20"
              onClick={() => setShowForm(v => !v)}
            >
              <Upload size={12} />
              Drop PRD
            </button>

            {/* Build Rules gear */}
            <button
              onClick={() => setRulesOpen(v => !v)}
              className={`h-7 w-7 rounded flex items-center justify-center transition-colors ${
                rulesOpen
                  ? 'text-emerald-400 bg-emerald-500/15 hover:bg-emerald-500/25'
                  : 'text-zinc-500 hover:text-white hover:bg-zinc-800'
              }`}
              title="Build Rules"
            >
              <Settings size={14} />
            </button>

            {/* Dark/light toggle */}
            <button
              onClick={toggleDarkMode}
              className="h-7 w-7 rounded flex items-center justify-center text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors"
              title="Toggle dark mode"
            >
              {darkMode ? <Sun size={14} /> : <Moon size={14} />}
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-5 space-y-5">

        {/* Build Rules panel — slides down from header */}
        <BuildRulesPanel isOpen={rulesOpen} onClose={() => setRulesOpen(false)} />

        {/* Enqueue form */}
        {showForm && <EnqueueForm onClose={() => setShowForm(false)} />}

        {/* Empty state */}
        {!hasContent && !showForm && (
          <div className="bg-zinc-100 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-700/60 rounded-xl p-12 flex flex-col items-center justify-center text-zinc-500">
            <div className="w-14 h-14 rounded-xl bg-zinc-200/50 dark:bg-zinc-700/30 border border-zinc-300/50 dark:border-zinc-600/30 flex items-center justify-center mb-4">
              <FileText size={24} className="text-zinc-400 dark:text-zinc-600" />
            </div>
            <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">No PRDs in the shredder</p>
            <p className="text-xs mt-1 text-zinc-400 dark:text-zinc-600">Drop a PRD to start building</p>
          </div>
        )}

        {/* ====== SECTION 1: Active Build — orange border ====== */}
        {activeItems.length > 0 && (
          <section>
            <SectionCard
              icon={<Activity size={16} className="text-orange-400" />}
              title="Building Now"
              count={activeItems.length}
              accent="border-orange-500/30"
            >
              <div className="space-y-3 -mx-5 -mb-5">
                {activeItems.map(item => (
                  <ActiveBuildCard key={item.id} item={item} />
                ))}
              </div>
            </SectionCard>
          </section>
        )}

        {/* ====== SECTION 2: Queue — amber border ====== */}
        {queuedItems.length > 0 && (
          <SectionCard
            icon={<ListOrdered size={16} className="text-amber-400" />}
            title="Up Next"
            count={queuedItems.length}
            accent="border-amber-500/30"
          >
            <div className="space-y-1.5">
              {queuedItems.map((item, idx) => (
                <QueueRow
                  key={item.id}
                  item={item}
                  position={idx + 1}
                  onDelete={id => deleteItem.mutate(id)}
                />
              ))}
            </div>
          </SectionCard>
        )}

        {/* ====== SECTION 3: History — cyan border ====== */}
        {historyItems.length > 0 && (
          <SectionCard
            icon={<History size={16} className="text-cyan-400" />}
            title="History"
            count={historyItems.length}
            accent="border-cyan-500/30"
          >
            <div className="space-y-1.5 max-h-[500px] overflow-y-auto pr-1">
              {historyItems.map(item => (
                <HistoryRow
                  key={item.id}
                  item={item}
                  onRetry={id => retryItem.mutate(id)}
                  onDelete={id => deleteItem.mutate(id)}
                />
              ))}
            </div>
          </SectionCard>
        )}
      </div>
    </div>
  )
}
