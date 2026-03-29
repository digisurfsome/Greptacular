/**
 * GapAnalysisPanel Component
 *
 * Gap display panel with severity groups and resolution controls.
 * Shows blocking, important, and resolved gaps with action buttons.
 */

import { useState, useCallback } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Wand2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import type { AgentOSGapItem } from '@/hooks/useAgentOS'

// ============================================================================
// Types
// ============================================================================

interface GapAnalysisPanelProps {
  gaps: AgentOSGapItem[]
  onResolveGap: (gapId: number, resolution: string) => void
  onAutoResolve: () => void
}

// ============================================================================
// Component
// ============================================================================

export function GapAnalysisPanel({
  gaps,
  onResolveGap,
  onAutoResolve,
}: GapAnalysisPanelProps) {
  const blocking = gaps.filter(g => g.severity === 'blocking' && !g.resolved)
  const important = gaps.filter(g => g.severity !== 'blocking' && !g.resolved)
  const resolved = gaps.filter(g => g.resolved)
  const [resolvedExpanded, setResolvedExpanded] = useState(false)

  if (gaps.length === 0) {
    return (
      <Card>
        <CardContent className="p-4 text-center">
          <CheckCircle2 size={20} className="mx-auto text-green-500 mb-2" />
          <p className="text-xs text-muted-foreground">No gaps detected</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="p-0">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-border">
          <div className="flex items-center gap-2">
            <AlertTriangle size={14} className="text-amber-500" />
            <span className="text-xs font-bold text-foreground">Gap Analysis</span>
            <span className="text-[10px] text-muted-foreground">({gaps.length})</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="h-6 text-[10px]"
            onClick={onAutoResolve}
            title="Auto-resolve high-confidence gaps"
          >
            <Wand2 size={10} />
            Auto-Resolve
          </Button>
        </div>

        {/* Blocking gaps */}
        {blocking.length > 0 && (
          <div className="px-3 py-2">
            <div className="flex items-center gap-1.5 mb-2">
              <AlertCircle size={12} className="text-red-500" />
              <span className="text-[10px] font-bold text-red-500 uppercase">
                Blocking ({blocking.length})
              </span>
            </div>
            <div className="space-y-2">
              {blocking.map(gap => (
                <GapItem key={gap.id} gap={gap} onResolve={onResolveGap} />
              ))}
            </div>
          </div>
        )}

        {/* Important / other gaps */}
        {important.length > 0 && (
          <div className="px-3 py-2 border-t border-border/50">
            <div className="flex items-center gap-1.5 mb-2">
              <AlertTriangle size={12} className="text-amber-500" />
              <span className="text-[10px] font-bold text-amber-500 uppercase">
                Open ({important.length})
              </span>
            </div>
            <div className="space-y-2">
              {important.map(gap => (
                <GapItem key={gap.id} gap={gap} onResolve={onResolveGap} />
              ))}
            </div>
          </div>
        )}

        {/* Resolved gaps */}
        {resolved.length > 0 && (
          <div className="px-3 py-2 border-t border-border/50">
            <button
              onClick={() => setResolvedExpanded(prev => !prev)}
              className="flex items-center gap-1.5 w-full text-left"
            >
              {resolvedExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              <CheckCircle2 size={12} className="text-green-500" />
              <span className="text-[10px] font-bold text-green-500 uppercase">
                Resolved ({resolved.length})
              </span>
            </button>
            {resolvedExpanded && (
              <div className="mt-2 space-y-1">
                {resolved.map(gap => (
                  <div key={gap.id} className="text-[10px] text-muted-foreground pl-5">
                    Gap #{gap.id}: {gap.message}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Gap item sub-component
// ============================================================================

function GapItem({
  gap,
  onResolve,
}: {
  gap: AgentOSGapItem
  onResolve: (gapId: number, resolution: string) => void
}) {
  const [showCustom, setShowCustom] = useState(false)
  const [customResolution, setCustomResolution] = useState('')

  const handleAcceptRecommendation = useCallback(() => {
    onResolve(gap.id, gap.recommendation)
  }, [gap, onResolve])

  const handleCustomResolve = useCallback(() => {
    if (!customResolution.trim()) return
    onResolve(gap.id, customResolution.trim())
    setCustomResolution('')
    setShowCustom(false)
  }, [gap.id, customResolution, onResolve])

  return (
    <div className="border border-border rounded-lg p-2.5 bg-card">
      <p className="text-xs text-foreground leading-snug">{gap.message}</p>

      {gap.recommendation && (
        <p className="text-[10px] text-muted-foreground mt-1.5">
          Recommendation: {gap.recommendation}
          {gap.confidence > 0 && (
            <span className="ml-1 text-primary font-bold">({Math.round(gap.confidence * 100)}%)</span>
          )}
        </p>
      )}

      <div className="flex flex-wrap gap-1.5 mt-2">
        {gap.recommendation && (
          <Button
            variant="outline"
            size="sm"
            className="h-5 text-[9px] px-2"
            onClick={handleAcceptRecommendation}
          >
            Accept
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="h-5 text-[9px] px-2"
          onClick={() => setShowCustom(prev => !prev)}
        >
          Custom
        </Button>
      </div>

      {showCustom && (
        <div className="flex gap-1.5 mt-2">
          <Input
            className="h-6 text-[10px]"
            placeholder="Your resolution..."
            value={customResolution}
            onChange={e => setCustomResolution(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCustomResolve()}
          />
          <Button size="sm" className="h-6 text-[9px] px-2" onClick={handleCustomResolve}>
            OK
          </Button>
        </div>
      )}
    </div>
  )
}
