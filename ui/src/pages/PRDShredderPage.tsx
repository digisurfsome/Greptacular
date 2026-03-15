import { useState, useRef } from 'react'
import { ArrowLeft, Upload, RotateCcw, Trash2, ChevronDown, ChevronRight, FileText, Loader2, CheckCircle2, XCircle, Clock, Zap, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
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

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  queued: { label: 'Queued', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', icon: <Clock size={12} /> },
  cloning: { label: 'Cloning', color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30', icon: <Loader2 size={12} className="animate-spin" /> },
  analyzing: { label: 'Analyzing', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: <Loader2 size={12} className="animate-spin" /> },
  building: { label: 'Building', color: 'bg-purple-500/20 text-purple-400 border-purple-500/30', icon: <Loader2 size={12} className="animate-spin" /> },
  testing: { label: 'Testing', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', icon: <Loader2 size={12} className="animate-spin" /> },
  committing: { label: 'Committing', color: 'bg-teal-500/20 text-teal-400 border-teal-500/30', icon: <Loader2 size={12} className="animate-spin" /> },
  qa_testing: { label: 'QA Testing', color: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30', icon: <Loader2 size={12} className="animate-spin" /> },
  done: { label: 'Done', color: 'bg-green-500/20 text-green-400 border-green-500/30', icon: <CheckCircle2 size={12} /> },
  failed: { label: 'Failed', color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: <XCircle size={12} /> },
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || { label: status, color: 'bg-muted text-muted-foreground border-border', icon: null }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded border ${cfg.color}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  )
}

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

function StatsBar({ stats }: { stats: { total: number; queued: number; building: number; done: number; failed: number } }) {
  return (
    <div className="flex items-center gap-3 text-xs">
      <span className="text-muted-foreground">{stats.total} total</span>
      {stats.queued > 0 && <span className="text-yellow-400">{stats.queued} queued</span>}
      {stats.building > 0 && <span className="text-purple-400">{stats.building} building</span>}
      {stats.done > 0 && <span className="text-green-400">{stats.done} done</span>}
      {stats.failed > 0 && <span className="text-red-400">{stats.failed} failed</span>}
    </div>
  )
}

function LogViewer({ itemId }: { itemId: string }) {
  const { data } = useShredderItemLogs(itemId)
  const containerRef = useRef<HTMLDivElement>(null)

  const logs = data?.logs || []

  return (
    <div
      ref={containerRef}
      className="bg-black/50 rounded border border-border p-2 max-h-64 overflow-y-auto font-mono text-[11px] leading-relaxed"
    >
      {logs.length === 0 ? (
        <span className="text-muted-foreground">No logs yet...</span>
      ) : (
        logs.map((line, i) => (
          <div key={i} className="text-muted-foreground hover:text-foreground transition-colors">
            {line}
          </div>
        ))
      )}
    </div>
  )
}

function QueueItem({
  item,
  isExpanded,
  onToggle,
  onRetry,
  onDelete,
}: {
  item: ShredderQueueItem
  isExpanded: boolean
  onToggle: () => void
  onRetry: (id: string) => void
  onDelete: (id: string) => void
}) {
  const isActive = ['cloning', 'analyzing', 'building', 'testing', 'committing', 'qa_testing'].includes(item.status)
  const progress = item.tasks_total > 0 ? Math.round((item.tasks_done / item.tasks_total) * 100) : 0

  return (
    <div className={`border rounded-lg transition-colors ${isActive ? 'border-purple-500/40 bg-purple-500/5' : 'border-border bg-card'}`}>
      {/* Row */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-muted/30 transition-colors"
        onClick={onToggle}
      >
        <span className="text-muted-foreground">
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground truncate">{item.title}</span>
            <StatusBadge status={item.status} />
          </div>
          <div className="flex items-center gap-3 mt-0.5">
            <span className="text-[11px] text-muted-foreground truncate max-w-48">
              {item.target_repo.split('/').pop() || item.target_repo}
            </span>
            {item.tasks_total > 0 && (
              <span className="text-[11px] text-muted-foreground">
                {item.tasks_done}/{item.tasks_total} tasks
              </span>
            )}
            {item.commit_hash && (
              <span className="text-[11px] text-green-400 font-mono">{item.commit_hash}</span>
            )}
            <span className="text-[11px] text-muted-foreground">{relativeTime(item.created_at)}</span>
          </div>
        </div>

        {/* Progress bar for active items */}
        {isActive && item.tasks_total > 0 && (
          <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-purple-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
          {item.status === 'failed' && (
            <Button variant="ghost" size="sm" className="h-7 px-2 text-yellow-400 hover:text-yellow-300" onClick={() => onRetry(item.id)} title="Retry">
              <RotateCcw size={13} />
            </Button>
          )}
          {['queued', 'done', 'failed'].includes(item.status) && (
            <Button variant="ghost" size="sm" className="h-7 px-2 text-muted-foreground hover:text-red-400" onClick={() => onDelete(item.id)} title="Delete">
              <Trash2 size={13} />
            </Button>
          )}
        </div>
      </div>

      {/* Expanded: Logs + Error */}
      {isExpanded && (
        <div className="px-3 pb-3 space-y-2">
          {item.error && (
            <div className="flex items-start gap-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              <span>{item.error}</span>
            </div>
          )}
          {item.playwright_errors.length > 0 && (
            <div className="p-2 bg-orange-500/10 border border-orange-500/20 rounded text-xs text-orange-400">
              <span className="font-medium">Playwright found {item.playwright_errors.length} error(s)</span>
              {item.bugfix_prd_id && (
                <span className="ml-2 text-muted-foreground">Bug-fix PRD queued</span>
              )}
            </div>
          )}
          <LogViewer itemId={item.id} />
        </div>
      )}
    </div>
  )
}

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
    <div className="border border-border rounded-lg bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">Drop a PRD</h3>
        <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={onClose}>Cancel</Button>
      </div>

      <input
        type="text"
        placeholder="PRD title"
        value={title}
        onChange={e => setTitle(e.target.value)}
        className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded focus:outline-none focus:border-foreground/30"
      />

      <input
        type="text"
        placeholder="Target repo path (e.g. C:\Users\lober\GitHub\...)"
        value={targetRepo}
        onChange={e => setTargetRepo(e.target.value)}
        className="w-full px-3 py-1.5 text-sm bg-background border border-border rounded focus:outline-none focus:border-foreground/30"
      />

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-1.5 text-xs"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={13} />
          Upload .md file
        </Button>
        <input ref={fileInputRef} type="file" accept=".md,.txt" className="hidden" onChange={handleFileUpload} />
        {prdText && <span className="text-[11px] text-green-400">{prdText.length.toLocaleString()} chars loaded</span>}
      </div>

      {!prdText && (
        <textarea
          placeholder="Or paste PRD text here..."
          value={prdText}
          onChange={e => setPrdText(e.target.value)}
          rows={6}
          className="w-full px-3 py-2 text-xs font-mono bg-background border border-border rounded resize-y focus:outline-none focus:border-foreground/30"
        />
      )}

      <div className="flex justify-end">
        <Button
          size="sm"
          className="h-8 gap-1.5 text-xs bg-purple-600 hover:bg-purple-500 text-white"
          onClick={handleSubmit}
          disabled={!title.trim() || !prdText.trim() || !targetRepo.trim() || enqueue.isPending}
        >
          {enqueue.isPending ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
          Shred It
        </Button>
      </div>
    </div>
  )
}

export function PRDShredderPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const { data: queueData } = useShredderQueue()
  const { data: stats } = useShredderStats()
  const { data: status } = useShredderStatus()
  const retryItem = useRetryItem()
  const retryAll = useRetryAllFailed()
  const deleteItem = useDeleteItem()

  const items = queueData?.items || []
  const failedCount = stats?.failed || 0

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0 gap-2">
        <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => { window.location.hash = '' }}>
          <ArrowLeft size={14} />
        </Button>
        <FileText size={16} className="text-purple-400" />
        <span className="text-sm font-medium text-foreground">PRD Shredder</span>
        <span className={`ml-1 w-2 h-2 rounded-full ${status?.running ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} title={status?.running ? 'Running' : 'Stopped'} />

        <div className="flex-1" />

        {stats && <StatsBar stats={stats} />}

        {failedCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-[11px] gap-1 text-yellow-400 border-yellow-500/30"
            onClick={() => retryAll.mutate()}
            disabled={retryAll.isPending}
          >
            <RotateCcw size={12} />
            Retry {failedCount} failed
          </Button>
        )}

        <Button
          size="sm"
          className="h-7 text-[11px] gap-1 bg-purple-600 hover:bg-purple-500 text-white"
          onClick={() => setShowForm(v => !v)}
        >
          <Upload size={12} />
          Drop PRD
        </Button>
      </div>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-3 space-y-2">
        {showForm && (
          <EnqueueForm onClose={() => setShowForm(false)} />
        )}

        {items.length === 0 && !showForm && (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <FileText size={40} className="mb-3 opacity-30" />
            <p className="text-sm">No PRDs in the shredder</p>
            <p className="text-xs mt-1">Drop a PRD to start building</p>
          </div>
        )}

        {items.map(item => (
          <QueueItem
            key={item.id}
            item={item}
            isExpanded={expandedId === item.id}
            onToggle={() => setExpandedId(prev => prev === item.id ? null : item.id)}
            onRetry={id => retryItem.mutate(id)}
            onDelete={id => deleteItem.mutate(id)}
          />
        ))}
      </main>
    </div>
  )
}
