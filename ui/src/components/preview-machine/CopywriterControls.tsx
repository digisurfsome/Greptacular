/**
 * CopywriterControls — settings for stage 4 (Write copy).
 *
 * Plain-language controls for a non-coder: which model, how fast to drip-feed,
 * whether to auto-retry after a rate limit, and batch size. The parent owns the
 * state; this component is a controlled form.
 */

import { Switch } from '@/components/ui/switch'

/** The copywriter settings this control edits. */
export interface CopywriterSettings {
  model: 'sonnet' | 'haiku'
  /** Businesses per hour. 0 = full speed (no throttle). */
  perHour: number
  /** When on, wait and retry the same batch after a rate limit. */
  autoRetry: boolean
  /** Minutes to wait before retrying (only used when autoRetry is on). */
  autoRetryMinutes: number
  batchSize: number
}

interface CopywriterControlsProps {
  value: CopywriterSettings
  onChange: (next: CopywriterSettings) => void
  disabled?: boolean
}

const fieldLabel = 'text-xs font-medium text-foreground'
const helperText = 'text-xs text-muted-foreground mt-1'
const numberInput =
  'w-28 px-3 py-1.5 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary'

export function CopywriterControls({ value, onChange, disabled }: CopywriterControlsProps) {
  const set = <K extends keyof CopywriterSettings>(key: K, v: CopywriterSettings[K]) =>
    onChange({ ...value, [key]: v })

  return (
    <div className="bg-muted/40 rounded-lg border border-border p-4 space-y-4">
      <h4 className="text-sm font-semibold text-foreground">Copy settings</h4>

      {/* Model */}
      <div>
        <label className={fieldLabel} htmlFor="pm-model">
          Model
        </label>
        <select
          id="pm-model"
          className="block mt-1 w-40 px-3 py-1.5 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary"
          value={value.model}
          disabled={disabled}
          onChange={(e) => set('model', e.target.value as 'sonnet' | 'haiku')}
        >
          <option value="sonnet">Sonnet (better writing)</option>
          <option value="haiku">Haiku (faster, cheaper)</option>
        </select>
      </div>

      {/* Per hour drip-feed */}
      <div>
        <label className={fieldLabel} htmlFor="pm-perhour">
          Per hour
        </label>
        <input
          id="pm-perhour"
          type="number"
          min={0}
          className={`block mt-1 ${numberInput}`}
          value={value.perHour}
          disabled={disabled}
          onChange={(e) => set('perHour', Math.max(0, Number(e.target.value) || 0))}
        />
        <p className={helperText}>
          drip-feed: leave subscription headroom to keep working (0 = full speed)
        </p>
      </div>

      {/* Auto-retry */}
      <div>
        <div className="flex items-center gap-2">
          <Switch
            id="pm-autoretry"
            checked={value.autoRetry}
            disabled={disabled}
            onCheckedChange={(checked) =>
              onChange({
                ...value,
                autoRetry: checked,
                // Default to 60 minutes the first time it's switched on.
                autoRetryMinutes: checked && value.autoRetryMinutes === 0 ? 60 : value.autoRetryMinutes,
              })
            }
          />
          <label className={fieldLabel} htmlFor="pm-autoretry">
            Auto-retry after a rate limit
          </label>
        </div>
        {value.autoRetry && (
          <div className="mt-2">
            <input
              type="number"
              min={1}
              aria-label="Auto-retry minutes"
              className={numberInput}
              value={value.autoRetryMinutes}
              disabled={disabled}
              onChange={(e) => set('autoRetryMinutes', Math.max(1, Number(e.target.value) || 1))}
            />
            <span className="ml-2 text-xs text-muted-foreground">minutes</span>
          </div>
        )}
        <p className={helperText}>
          wait and retry the same batch after a rate limit — no more babysitting the 4-hour window
        </p>
      </div>

      {/* Batch size */}
      <div>
        <label className={fieldLabel} htmlFor="pm-batch">
          Batch size
        </label>
        <input
          id="pm-batch"
          type="number"
          min={1}
          className={`block mt-1 ${numberInput}`}
          value={value.batchSize}
          disabled={disabled}
          onChange={(e) => set('batchSize', Math.max(1, Number(e.target.value) || 1))}
        />
      </div>
    </div>
  )
}
