/**
 * CalibrationCard — figures out a safe "per hour" speed from the copywriter's
 * own run history (runlog.jsonl). The owner picks a target % of full speed,
 * clicks Calculate, and gets a suggested number plus the raw runlog so he can
 * do his own math.
 *
 * Nothing runs automatically — calibration is fetched only on button click.
 */

import { useState } from 'react'
import { Gauge, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useCalculateCalibration } from '@/hooks/usePreviewMachine'
import type { PreviewMachineRunlogEvent } from '@/lib/types'

interface CalibrationCardProps {
  /** Fill the copywriter "Per hour" input with the suggested number. */
  onUseSuggested: (perHour: number) => void
}

/** A labelled stat row inside the result panel. */
function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1 border-b border-border/50 last:border-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  )
}

export function CalibrationCard({ onUseSuggested }: CalibrationCardProps) {
  const [targetPct, setTargetPct] = useState(70)
  const calc = useCalculateCalibration()

  const data = calc.data
  const cal = data?.calibration
  const events: PreviewMachineRunlogEvent[] = data?.events ?? []

  return (
    <div className="bg-card rounded-lg border border-border p-6 shadow-sm space-y-4">
      <div className="flex items-center gap-2">
        <Gauge className="w-5 h-5 text-foreground" />
        <h3 className="text-lg font-semibold text-foreground">Find a safe speed</h3>
      </div>
      <p className="text-sm text-muted-foreground">
        Reads the copywriter&apos;s run history and suggests a &quot;per hour&quot; number that
        stays under your subscription ceiling.
      </p>

      <div className="flex items-end gap-3">
        <div>
          <label className="text-xs font-medium text-foreground" htmlFor="pm-target">
            Target % of full speed
          </label>
          <input
            id="pm-target"
            type="number"
            min={1}
            max={100}
            className="block mt-1 w-28 px-3 py-1.5 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary"
            value={targetPct}
            onChange={(e) =>
              setTargetPct(Math.min(100, Math.max(1, Number(e.target.value) || 1)))
            }
          />
        </div>
        <Button onClick={() => calc.mutate(targetPct)} disabled={calc.isPending}>
          {calc.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
          {calc.isPending ? 'Calculating...' : 'Calculate'}
        </Button>
      </div>

      {calc.isError && (
        <p className="text-sm text-destructive">{(calc.error as Error).message}</p>
      )}

      {cal && !cal.has_data && (
        <p className="text-sm text-muted-foreground">{cal.message}</p>
      )}

      {cal && cal.has_data && (
        <div className="space-y-4">
          <div className="bg-muted/40 rounded-lg border border-border p-4">
            <Stat label="Total written (all runs)" value={String(cal.total_written ?? 0)} />
            <Stat
              label="Pure speed"
              value={cal.capacity_per_hour != null ? `${cal.capacity_per_hour}/hr` : '—'}
            />
            {cal.limit_hit ? (
              <>
                <Stat label="Limit hit at" value={cal.limit_ts ?? '—'} />
                <Stat
                  label="Time from start"
                  value={cal.window_hours != null ? `${cal.window_hours} h` : '—'}
                />
                <Stat
                  label="Burn rate"
                  value={
                    cal.burn_rate_per_hour != null ? `${cal.burn_rate_per_hour}/hr` : '—'
                  }
                />
              </>
            ) : (
              <Stat label="Limit hit" value="not yet" />
            )}
          </div>

          {/* The big suggested number */}
          {cal.suggested_per_hour != null && (
            <div className="bg-primary/10 rounded-lg border border-primary/30 p-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-xs text-muted-foreground">Suggested per hour</div>
                <div className="text-3xl font-bold text-foreground">
                  {cal.suggested_per_hour}
                </div>
              </div>
              <Button onClick={() => onUseSuggested(cal.suggested_per_hour as number)}>
                Use this
              </Button>
            </div>
          )}

          {cal.message && <p className="text-sm text-muted-foreground">{cal.message}</p>}

          {/* Raw runlog so the owner can do his own math */}
          {events.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-2">Recent run events</h4>
              <div className="overflow-auto max-h-56 rounded-lg border border-border">
                <table className="w-full text-xs">
                  <thead className="bg-muted/60 sticky top-0">
                    <tr>
                      <th className="text-left px-3 py-2 font-medium text-muted-foreground">
                        Time
                      </th>
                      <th className="text-left px-3 py-2 font-medium text-muted-foreground">
                        Event
                      </th>
                      <th className="text-right px-3 py-2 font-medium text-muted-foreground">
                        Written
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((ev, idx) => (
                      <tr key={idx} className="border-t border-border/50">
                        <td className="px-3 py-1.5 text-muted-foreground whitespace-nowrap">
                          {String(ev.ts ?? '—')}
                        </td>
                        <td className="px-3 py-1.5 text-foreground">{String(ev.event ?? '—')}</td>
                        <td className="px-3 py-1.5 text-right text-foreground">
                          {ev.written != null ? String(ev.written) : ''}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
