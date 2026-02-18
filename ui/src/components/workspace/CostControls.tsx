/**
 * Cost Controls Panel
 *
 * Collapsible panel that gives the user fine-grained control over token cost
 * parameters for the workspace agent.  Settings are persisted to localStorage
 * and sent to the backend via the WebSocket "start" message.
 *
 * Think of it as a "stick shift" for API spend — every lever trades quality
 * or context for lower cost.
 */

import { useState, useCallback } from 'react'
import {
  ChevronDown,
  ChevronUp,
  Gauge,
  Brain,
  MessageSquare,
  BookOpen,
  Repeat,
  Zap,
} from 'lucide-react'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CostSettings {
  effort: 'low' | 'medium' | 'high'
  max_tokens: number
  max_turns: number
  history_budget: number
  library_cap: number
}

export const DEFAULT_COST_SETTINGS: CostSettings = {
  effort: 'low',
  max_tokens: 16384,
  max_turns: 50,
  history_budget: 100_000,
  library_cap: 50_000,
}

const PRESETS: Record<string, { label: string; icon: React.ReactNode; settings: CostSettings; description: string }> = {
  economy: {
    label: 'Economy',
    icon: <Gauge size={13} />,
    description: 'Lowest cost. Fast answers, less thinking.',
    settings: { effort: 'low', max_tokens: 8192, max_turns: 25, history_budget: 50_000, library_cap: 25_000 },
  },
  balanced: {
    label: 'Balanced',
    icon: <Zap size={13} />,
    description: 'Good balance of quality and cost.',
    settings: { effort: 'low', max_tokens: 16384, max_turns: 50, history_budget: 100_000, library_cap: 50_000 },
  },
  performance: {
    label: 'Performance',
    icon: <Brain size={13} />,
    description: 'Higher quality, deeper thinking. Costs more.',
    settings: { effort: 'medium', max_tokens: 32768, max_turns: 75, history_budget: 200_000, library_cap: 100_000 },
  },
  max: {
    label: 'Max Quality',
    icon: <Brain size={13} />,
    description: 'Full power. Highest cost.',
    settings: { effort: 'high', max_tokens: 65536, max_turns: 100, history_budget: 400_000, library_cap: 200_000 },
  },
}

const STORAGE_KEY = 'workspace-cost-settings'

export function loadCostSettings(): CostSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return { ...DEFAULT_COST_SETTINGS, ...parsed }
    }
  } catch { /* ignore */ }
  return { ...DEFAULT_COST_SETTINGS }
}

export function saveCostSettings(settings: CostSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`
  return String(n)
}

/** Estimate $/session based on settings (very rough ballpark). */
function estimateCostRange(s: CostSettings): string {
  // Input cost estimate: history + library + avg tool results per turn
  const avgToolResultTokens = 3000  // avg tokens from tool calls per turn
  const inputPerTurn = s.history_budget + s.library_cap + avgToolResultTokens
  const inputTotal = inputPerTurn + (s.max_turns * avgToolResultTokens)

  // Output cost estimate: response tokens + thinking tokens (effort multiplier)
  const effortMultiplier = s.effort === 'low' ? 0.3 : s.effort === 'medium' ? 0.7 : 1.5
  const avgOutputPerTurn = (s.max_tokens * 0.3) + (s.max_tokens * effortMultiplier * 0.5)
  const outputTotal = s.max_turns * avgOutputPerTurn * 0.4  // assume 40% of max turns used

  // Opus 4.6 pricing: $5/MTok input, $25/MTok output (standard zone)
  const inputCost = (inputTotal / 1_000_000) * 5
  const outputCost = (outputTotal / 1_000_000) * 25

  const low = Math.max(0.05, (inputCost + outputCost) * 0.3)
  const high = inputCost + outputCost

  if (high < 0.10) return '<$0.10'
  return `$${low.toFixed(2)}-$${high.toFixed(2)}`
}

function getActivePreset(settings: CostSettings): string | null {
  for (const [key, preset] of Object.entries(PRESETS)) {
    const p = preset.settings
    if (
      p.effort === settings.effort &&
      p.max_tokens === settings.max_tokens &&
      p.max_turns === settings.max_turns &&
      p.history_budget === settings.history_budget &&
      p.library_cap === settings.library_cap
    ) return key
  }
  return null
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function EffortSelector({ value, onChange }: { value: string; onChange: (v: 'low' | 'medium' | 'high') => void }) {
  const levels: { key: 'low' | 'medium' | 'high'; label: string; cost: string }[] = [
    { key: 'low', label: 'Low', cost: '$' },
    { key: 'medium', label: 'Med', cost: '$$' },
    { key: 'high', label: 'High', cost: '$$$' },
  ]
  return (
    <div className="flex gap-1">
      {levels.map(l => (
        <button
          key={l.key}
          onClick={() => onChange(l.key)}
          className={`px-2.5 py-1 text-[10px] font-medium rounded-md border transition-all ${
            value === l.key
              ? 'bg-primary text-primary-foreground border-primary shadow-sm'
              : 'bg-muted/50 text-muted-foreground border-border hover:bg-muted'
          }`}
        >
          {l.label} <span className="opacity-60">{l.cost}</span>
        </button>
      ))}
    </div>
  )
}

function SliderControl({
  label,
  icon,
  value,
  min,
  max,
  step,
  format,
  hint,
  onChange,
}: {
  label: string
  icon: React.ReactNode
  value: number
  min: number
  max: number
  step: number
  format: (v: number) => string
  hint: string
  onChange: (v: number) => void
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-muted-foreground">
          {icon}
          <span className="text-[10px] font-medium">{label}</span>
        </div>
        <span className="text-[10px] font-mono text-foreground">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-muted rounded-full appearance-none cursor-pointer
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-sm
          [&::-webkit-slider-thumb]:border [&::-webkit-slider-thumb]:border-primary/50
          [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:rounded-full
          [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border [&::-moz-range-thumb]:border-primary/50"
      />
      <p className="text-[9px] text-muted-foreground/70">{hint}</p>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

interface CostControlsProps {
  settings: CostSettings
  onChange: (settings: CostSettings) => void
}

export default function CostControls({ settings, onChange }: CostControlsProps) {
  const [expanded, setExpanded] = useState(false)
  const activePreset = getActivePreset(settings)

  const update = useCallback(
    (patch: Partial<CostSettings>) => {
      const next = { ...settings, ...patch }
      saveCostSettings(next)
      onChange(next)
    },
    [settings, onChange],
  )

  const applyPreset = useCallback(
    (key: string) => {
      const preset = PRESETS[key]
      if (preset) {
        saveCostSettings(preset.settings)
        onChange(preset.settings)
      }
    },
    [onChange],
  )

  const costEstimate = estimateCostRange(settings)

  return (
    <div className="border-b border-border bg-card/50">
      {/* Collapsed summary row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-[11px] hover:bg-muted/50 transition-colors"
      >
        <Gauge size={12} className="text-muted-foreground flex-shrink-0" />
        <span className="text-muted-foreground font-medium">Cost Controls</span>

        {/* Active preset badge */}
        <span className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${
          activePreset === 'economy' ? 'bg-emerald-500/15 text-emerald-400' :
          activePreset === 'balanced' ? 'bg-blue-500/15 text-blue-400' :
          activePreset === 'performance' ? 'bg-orange-500/15 text-orange-400' :
          activePreset === 'max' ? 'bg-red-500/15 text-red-400' :
          'bg-purple-500/15 text-purple-400'
        }`}>
          {activePreset ? PRESETS[activePreset].label : 'Custom'}
        </span>

        <span className="text-[9px] text-muted-foreground/60 ml-auto mr-1">
          est. {costEstimate}/session
        </span>

        {expanded ? <ChevronUp size={12} className="text-muted-foreground" /> : <ChevronDown size={12} className="text-muted-foreground" />}
      </button>

      {/* Expanded panel */}
      {expanded && (
        <div className="px-3 pb-3 space-y-3 border-t border-border/50 pt-2">
          {/* Preset buttons */}
          <div className="space-y-1">
            <span className="text-[9px] font-medium text-muted-foreground uppercase tracking-wider">Presets</span>
            <div className="grid grid-cols-4 gap-1.5">
              {Object.entries(PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => applyPreset(key)}
                  className={`flex flex-col items-center gap-0.5 px-2 py-1.5 rounded-md border text-[10px] transition-all ${
                    activePreset === key
                      ? 'bg-primary/10 border-primary/40 text-foreground shadow-sm'
                      : 'bg-muted/30 border-border text-muted-foreground hover:bg-muted/60'
                  }`}
                  title={preset.description}
                >
                  {preset.icon}
                  <span className="font-medium">{preset.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Fine-grained controls */}
          <div className="space-y-2.5">
            <span className="text-[9px] font-medium text-muted-foreground uppercase tracking-wider">Fine-tune</span>

            {/* Thinking Effort */}
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Brain size={11} />
                <span className="text-[10px] font-medium">Thinking Effort</span>
              </div>
              <EffortSelector value={settings.effort} onChange={v => update({ effort: v })} />
              <p className="text-[9px] text-muted-foreground/70">
                Controls invisible &quot;thinking&quot; tokens billed at $25/MTok output rate. Low = cheapest.
              </p>
            </div>

            {/* Max Output Tokens */}
            <SliderControl
              label="Max Response Length"
              icon={<MessageSquare size={11} />}
              value={settings.max_tokens}
              min={4096}
              max={65536}
              step={4096}
              format={formatTokens}
              hint="Cap on output tokens per response. Shorter = cheaper."
              onChange={v => update({ max_tokens: v })}
            />

            {/* Max Turns */}
            <SliderControl
              label="Max Turns"
              icon={<Repeat size={11} />}
              value={settings.max_turns}
              min={10}
              max={100}
              step={5}
              format={v => String(v)}
              hint="Max agent tool-call rounds per message. Lower = fewer operations."
              onChange={v => update({ max_turns: v })}
            />

            {/* History Budget */}
            <SliderControl
              label="History Budget"
              icon={<BookOpen size={11} />}
              value={settings.history_budget}
              min={25000}
              max={400000}
              step={25000}
              format={formatTokens}
              hint="Tokens of past conversation loaded on resume. Above 200K triggers premium pricing."
              onChange={v => update({ history_budget: v })}
            />

            {/* Library File Cap */}
            <SliderControl
              label="Library File Cap"
              icon={<BookOpen size={11} />}
              value={settings.library_cap}
              min={10000}
              max={200000}
              step={10000}
              format={formatTokens}
              hint="Max tokens injected from library files per message."
              onChange={v => update({ library_cap: v })}
            />
          </div>

          {/* Cost explainer */}
          <div className="bg-muted/30 rounded-md p-2 text-[9px] text-muted-foreground/80 space-y-1">
            <p><strong>How costs work:</strong> Every token you send (input) and receive (output) costs money.</p>
            <p>Opus 4.6: <strong>$5/MTok</strong> input, <strong>$25/MTok</strong> output. Above 200K input, prices jump 50-100%.</p>
            <p>Thinking tokens are invisible but billed as output. &quot;Low&quot; effort minimizes these.</p>
            <p>Settings take effect on the <strong>next session start</strong> (new chat or reconnect).</p>
          </div>
        </div>
      )}
    </div>
  )
}
