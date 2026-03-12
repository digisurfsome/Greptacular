/**
 * BuildLibrary — Save, load, and delete build configurations.
 *
 * A collapsible panel showing saved builds with search, timestamps,
 * and Load/Queue/Delete actions per config.
 */

import { useState, useEffect, useCallback } from 'react'
import { Loader2, Search, BookOpen, Trash2, Download, Plus, Check, X } from 'lucide-react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BuildConfigMeta {
  id: number
  name: string
  created_at: string
  updated_at: string
  status: string
  scripts_dir: string | null
  project_dir: string | null
  phase_count: number | null
  notes: string | null
}

export interface BuildConfigFull extends BuildConfigMeta {
  config_json: Record<string, unknown>
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.DEV ? 'http://localhost:8888' : ''

function relativeTime(isoStr: string): string {
  const then = new Date(isoStr).getTime()
  const now = Date.now()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function statusColor(status: string): string {
  switch (status) {
    case 'completed': return 'text-green-400 bg-green-900/30'
    case 'building': return 'text-cyan-400 bg-cyan-900/30 animate-pulse'
    case 'failed': return 'text-red-400 bg-red-900/30'
    case 'queued': return 'text-amber-400 bg-amber-900/30'
    default: return 'text-zinc-400 bg-zinc-800'
  }
}

function statusIcon(status: string): string {
  switch (status) {
    case 'completed': return '✅'
    case 'building': return '🔵'
    case 'failed': return '🔴'
    case 'queued': return '⏳'
    default: return '📝'
  }
}

// ---------------------------------------------------------------------------
// BuildLibrary component
// ---------------------------------------------------------------------------

interface BuildLibraryProps {
  /** Called when the user clicks Load — parent should populate form state */
  onLoad: (config: BuildConfigFull) => void
  /** Called when the user saves current form state */
  onSaveRequest: () => Promise<{ name: string; config_json: Record<string, unknown>; project_dir?: string; phase_count?: number } | null>
  /** Show/hide the panel */
  open: boolean
  onToggle: () => void
}

export function BuildLibrary({ onLoad, onSaveRequest, open, onToggle }: BuildLibraryProps) {
  const [configs, setConfigs] = useState<BuildConfigMeta[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [savingName, setSavingName] = useState('')
  const [showSaveInput, setShowSaveInput] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchConfigs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/cli-scripter/configs`)
      if (!res.ok) throw new Error('Failed to load configs')
      const data = await res.json()
      setConfigs(data.configs || [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (open) fetchConfigs()
  }, [open, fetchConfigs])

  const handleLoad = async (id: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/cli-scripter/configs/${id}`)
      if (!res.ok) throw new Error('Failed to load config')
      const config: BuildConfigFull = await res.json()
      onLoad(config)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load config')
    }
  }

  const handleDelete = async (id: number) => {
    if (deletingId !== id) {
      setDeletingId(id)
      return
    }
    try {
      const res = await fetch(`${API_BASE}/api/cli-scripter/configs/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete')
      setConfigs(prev => prev.filter(c => c.id !== id))
      setDeletingId(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete')
    }
  }

  const handleSave = async () => {
    if (!savingName.trim()) return
    setSaving(true)
    setError(null)
    try {
      const payload = await onSaveRequest()
      if (!payload) return
      const res = await fetch(`${API_BASE}/api/cli-scripter/configs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: savingName.trim(),
          config_json: payload.config_json,
          project_dir: payload.project_dir,
          phase_count: payload.phase_count,
          status: 'draft',
        }),
      })
      if (!res.ok) throw new Error('Failed to save config')
      setSavingName('')
      setShowSaveInput(false)
      await fetchConfigs()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const filtered = configs.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="border border-zinc-700/60 rounded-xl overflow-hidden">
      {/* Header toggle */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-zinc-800/40 hover:bg-zinc-800/60 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-orange-400" />
          <span className="text-sm font-medium text-white">Saved Builds</span>
          {configs.length > 0 && (
            <span className="text-xs text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded-full">
              {configs.length}
            </span>
          )}
        </div>
        <span className="text-xs text-zinc-500">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="p-4 space-y-3 bg-zinc-900/20">
          {/* Search + Save row */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search builds..."
                className="w-full bg-zinc-900 border border-zinc-700 rounded-lg pl-7 pr-3 py-1.5 text-white text-xs focus:border-orange-500 focus:outline-none transition-colors"
              />
            </div>
            <button
              onClick={() => setShowSaveInput(!showSaveInput)}
              className="flex items-center gap-1.5 bg-orange-600/20 border border-orange-700/40 rounded-lg px-3 py-1.5 text-orange-300 hover:bg-orange-600/30 transition-all text-xs"
            >
              <Plus size={12} />
              Save Current
            </button>
          </div>

          {/* Save input */}
          {showSaveInput && (
            <div className="flex gap-2">
              <input
                type="text"
                value={savingName}
                onChange={e => setSavingName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSave()}
                placeholder="Name this build config..."
                autoFocus
                className="flex-1 bg-zinc-900 border border-orange-700/40 rounded-lg px-3 py-1.5 text-white text-xs focus:border-orange-500 focus:outline-none transition-colors"
              />
              <button
                onClick={handleSave}
                disabled={saving || !savingName.trim()}
                className="flex items-center gap-1 bg-orange-500/80 rounded-lg px-3 py-1.5 text-white text-xs hover:bg-orange-500 transition-colors disabled:opacity-50"
              >
                {saving ? <Loader2 size={11} className="animate-spin" /> : <Check size={11} />}
                Save
              </button>
              <button
                onClick={() => { setShowSaveInput(false); setSavingName('') }}
                className="text-zinc-500 hover:text-zinc-300 transition-colors px-2"
              >
                <X size={13} />
              </button>
            </div>
          )}

          {error && (
            <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-1.5">{error}</p>
          )}

          {/* Config list */}
          {loading ? (
            <div className="flex items-center gap-2 text-xs text-zinc-500 py-4 justify-center">
              <Loader2 size={13} className="animate-spin" />
              Loading...
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-6 text-zinc-600 text-xs">
              {configs.length === 0 ? 'No saved builds yet. Click "Save Current" to save your first config.' : 'No results for your search.'}
            </div>
          ) : (
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {filtered.map(config => (
                <div key={config.id} className="bg-zinc-900/60 border border-zinc-800 rounded-lg px-3 py-2.5 space-y-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-sm">{statusIcon(config.status)}</span>
                      <span className="text-sm font-medium text-white truncate">{config.name}</span>
                    </div>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full shrink-0 ${statusColor(config.status)}`}>
                      {config.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-zinc-500">
                    <span>{relativeTime(config.updated_at)}</span>
                    {config.phase_count != null && config.phase_count > 0 && <span>{config.phase_count} phases</span>}
                    {config.project_dir && (
                      <span className="truncate max-w-[140px]" title={config.project_dir}>
                        {config.project_dir.split(/[/\\]/).pop()}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 pt-0.5">
                    <button
                      onClick={() => handleLoad(config.id)}
                      className="flex items-center gap-1 text-xs text-orange-400 hover:text-orange-300 border border-orange-700/40 rounded px-2 py-0.5 hover:border-orange-500/60 transition-all"
                    >
                      <Download size={10} />
                      Load
                    </button>
                    <button
                      onClick={() => handleDelete(config.id)}
                      className={`flex items-center gap-1 text-xs rounded px-2 py-0.5 transition-all ${
                        deletingId === config.id
                          ? 'text-red-300 border border-red-600/60 bg-red-900/20'
                          : 'text-zinc-500 hover:text-red-400 border border-zinc-700 hover:border-red-700/40'
                      }`}
                    >
                      <Trash2 size={10} />
                      {deletingId === config.id ? 'Confirm?' : 'Delete'}
                    </button>
                    {deletingId === config.id && (
                      <button
                        onClick={() => setDeletingId(null)}
                        className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
