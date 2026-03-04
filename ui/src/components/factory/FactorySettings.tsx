/**
 * FactorySettings - Modal for configuring factory mode parameters.
 *
 * Contains two tabs:
 *   1. Settings - Handoff threshold slider (35-55%) with warning/handoff/stop
 *      level indicators, and a handoff instructions template editor.
 *   2. Handoff History - Chronological list of past agent handoffs with
 *      phase info and summaries.
 *
 * Uses semantic Tailwind tokens for theme compatibility.
 * Follows the workspace modal pattern from DunkStackSafetyPanel.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  X,
  Save,
  RotateCcw,
  FileText,
  History,
  Loader2,
} from 'lucide-react'
import {
  useFactoryStatus,
  useFactorySettings,
  useFactoryHandoffs,
} from '../../hooks/useFactory'

/** Shape of a single handoff entry from the factory handoffs response. */
interface HandoffEntry {
  timestamp?: string
  phase?: { current?: number }
  completed?: { summary?: string }
  next_phase?: { summary?: string }
}

interface FactorySettingsProps {
  projectName: string | null
  onClose: () => void
}

export function FactorySettings({ projectName, onClose }: FactorySettingsProps): React.JSX.Element {
  const { data: statusResponse } = useFactoryStatus(projectName)
  const updateSettings = useFactorySettings(projectName)
  const { data: handoffsResponse } = useFactoryHandoffs(projectName)

  const statusData = statusResponse?.data as Record<string, unknown> | undefined
  const [threshold, setThreshold] = useState(45)
  const [template, setTemplate] = useState('')
  const [activeTab, setActiveTab] = useState<'settings' | 'history'>('settings')
  const [hasChanges, setHasChanges] = useState(false)

  // Sync local state when server data arrives
  useEffect(() => {
    if (statusData) {
      setThreshold(
        typeof statusData.handoff_threshold === 'number'
          ? statusData.handoff_threshold
          : 45,
      )
      setTemplate(
        typeof statusData.handoff_template === 'string'
          ? statusData.handoff_template
          : '',
      )
    }
  }, [statusData])

  // Derived threshold levels (same logic as DunkStackSafetyPanel tiers)
  const warningPct = Math.max(threshold - 10, 20)
  const handoffPct = Math.max(threshold - 5, 25)
  const stopPct = threshold

  const handleSave = useCallback(() => {
    updateSettings.mutate(
      { handoff_threshold: threshold, handoff_template: template },
      { onSuccess: () => setHasChanges(false) },
    )
  }, [updateSettings, threshold, template])

  const handleReset = useCallback(() => {
    setThreshold(45)
    setTemplate('')
    setHasChanges(true)
  }, [])

  // Close on Escape key
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  const handoffsData = handoffsResponse?.data as Record<string, unknown> | undefined
  const handoffs = (Array.isArray(handoffsData?.handoffs)
    ? handoffsData.handoffs
    : []) as HandoffEntry[]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-2xl max-h-[80vh] bg-card border border-border rounded-xl shadow-lg flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-sm font-bold text-foreground uppercase tracking-wide">
            Factory Settings
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-muted-foreground hover:text-foreground rounded hover:bg-muted transition-colors"
            aria-label="Close settings"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab bar */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'settings'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Settings
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'history'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Handoff History ({handoffs.length})
          </button>
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'settings' && (
            <div className="space-y-6">
              {/* Threshold Slider */}
              <div>
                <label className="block text-xs font-bold text-foreground mb-2 uppercase tracking-wide">
                  Handoff Threshold
                </label>
                <div className="space-y-2">
                  <input
                    type="range"
                    min={35}
                    max={55}
                    value={threshold}
                    onChange={(e) => {
                      setThreshold(Number(e.target.value))
                      setHasChanges(true)
                    }}
                    className="w-full accent-primary"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
                    <span>35%</span>
                    <span className="text-primary font-bold">{threshold}%</span>
                    <span>55%</span>
                  </div>

                  {/* Tier indicators -- mirrors DunkStackSafetyPanel style */}
                  <div className="flex gap-3 text-[11px]">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-amber-500" />
                      <span className="text-muted-foreground">
                        Warning: {warningPct}%
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-orange-500" />
                      <span className="text-muted-foreground">
                        Handoff: {handoffPct}%
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-red-500" />
                      <span className="text-muted-foreground">
                        Hard Stop: {stopPct}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Handoff Instructions Template */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold text-foreground uppercase tracking-wide">
                    Handoff Instructions
                  </label>
                  <button
                    onClick={handleReset}
                    className="flex items-center gap-1 px-2 py-0.5 text-[10px] text-muted-foreground hover:text-foreground border border-border rounded hover:bg-muted transition-colors"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Reset
                  </button>
                </div>
                <textarea
                  value={template}
                  onChange={(e) => {
                    setTemplate(e.target.value)
                    setHasChanges(true)
                  }}
                  rows={12}
                  className="w-full bg-background border border-border rounded-lg p-3 text-xs text-foreground font-mono resize-y focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary placeholder:text-muted-foreground"
                  placeholder="Enter handoff instructions template..."
                />
                <p className="mt-1 text-[10px] text-muted-foreground">
                  Placeholders: {'{warning_pct}'}, {'{handoff_pct}'},{' '}
                  {'{stop_pct}'}, {'{phase_num}'}, {'{phase_total}'},{' '}
                  {'{feature_list}'}
                </p>
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-2">
              {handoffs.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <History className="w-10 h-10 text-muted-foreground/40 mb-3" />
                  <p className="text-sm text-muted-foreground">
                    No handoffs yet
                  </p>
                  <p className="text-xs text-muted-foreground/60 mt-1">
                    Handoffs will appear here as the factory runs.
                  </p>
                </div>
              ) : (
                handoffs.map((h, i) => (
                  <div
                    key={`handoff-${i}`}
                    className="border border-border rounded-lg p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-foreground">
                        Phase {h.phase?.current ?? '?'}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {h.timestamp
                          ? new Date(h.timestamp).toLocaleString()
                          : 'Unknown time'}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {h.completed?.summary || 'No summary'}
                    </p>
                    {h.next_phase?.summary && (
                      <p className="text-[11px] text-muted-foreground/70 mt-1">
                        Next: {h.next_phase.summary}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer -- only show Save/Cancel for the settings tab */}
        {activeTab === 'settings' && (
          <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-border">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground border border-border rounded hover:bg-muted transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges || updateSettings.isPending}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold bg-primary hover:bg-primary/90 text-primary-foreground rounded border border-primary disabled:opacity-50 transition-colors"
            >
              {updateSettings.isPending ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Save className="w-3 h-3" />
              )}
              {updateSettings.isPending ? 'Saving...' : 'Save'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
