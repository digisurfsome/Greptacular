/**
 * RefreshIntervalSelector — Auto-refresh rate control for build monitoring.
 *
 * Simple toggle strip: [15s] [30s] [1m] [5m] [Off]
 * Controls how often the frontend polls the build-status endpoint.
 * Default: 30 seconds.
 */

interface RefreshIntervalSelectorProps {
  value: number // ms, 0 = off
  onChange: (ms: number) => void
}

const INTERVALS = [
  { label: '15s', ms: 15000 },
  { label: '30s', ms: 30000 },
  { label: '1m', ms: 60000 },
  { label: '5m', ms: 300000 },
  { label: 'Off', ms: 0 },
]

export function RefreshIntervalSelector({ value, onChange }: RefreshIntervalSelectorProps) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs text-zinc-500 mr-1">Refresh:</span>
      {INTERVALS.map((opt) => (
        <button
          key={opt.ms}
          onClick={() => onChange(opt.ms)}
          className={`text-[11px] px-2 py-0.5 rounded-md border transition-colors ${
            value === opt.ms
              ? 'border-orange-500/60 bg-orange-500/10 text-orange-300'
              : 'border-zinc-700/50 text-zinc-500 hover:text-zinc-300 hover:border-zinc-600'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
