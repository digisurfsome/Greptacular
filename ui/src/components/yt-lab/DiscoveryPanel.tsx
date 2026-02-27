/**
 * DiscoveryPanel — AI-powered opportunity discovery & evaluation.
 *
 * Sits between video ingestion and strategy extraction. Analyzes the video
 * to identify key insights, app opportunities, and strategic recommendations
 * so the user can make an informed decision about what to build.
 *
 * When the user selects an opportunity, that selection is passed up so it
 * can enrich the "Process Video" step with focused context.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import {
  Lightbulb,
  Rocket,
  Trophy,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Loader2,
  Search,
  Star,
  Zap,
  Target,
  TrendingUp,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import type {
  YTDiscoverResponse,
  YTAppOpportunity,
  YTKeyInsight,
  YTIngestResponse,
} from '@/lib/types'
import { discoverOpportunitiesStream } from '@/lib/api'
import type { DiscoveryLogEntry } from '@/lib/api'

// ---------------------------------------------------------------------------
// Score display helpers
// ---------------------------------------------------------------------------

function getScoreColor(score: number): string {
  if (score >= 90) return 'text-green-400'
  if (score >= 70) return 'text-emerald-400'
  if (score >= 50) return 'text-yellow-400'
  if (score >= 30) return 'text-orange-400'
  return 'text-red-400'
}

function getScoreBg(score: number): string {
  if (score >= 90) return 'bg-green-500/10 border-green-500/30'
  if (score >= 70) return 'bg-emerald-500/10 border-emerald-500/30'
  if (score >= 50) return 'bg-yellow-500/10 border-yellow-500/30'
  if (score >= 30) return 'bg-orange-500/10 border-orange-500/30'
  return 'bg-red-500/10 border-red-500/30'
}

function getScoreLabel(score: number): string {
  if (score >= 90) return 'No-brainer'
  if (score >= 70) return 'Strong'
  if (score >= 50) return 'Worth considering'
  if (score >= 30) return 'Weak'
  return 'Skip'
}

function getComplexityLabel(complexity: number): string {
  const labels: Record<number, string> = {
    1: 'Weekend project',
    2: 'Few days',
    3: 'A week or two',
    4: 'A month+',
    5: 'Major undertaking',
  }
  return labels[complexity] || 'Unknown'
}

function getTypeColor(type: string): string {
  const colors: Record<string, string> = {
    companion: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    direct: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    derivative: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    teaching: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  }
  return colors[type] || 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30'
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function InsightCard({ insight, index }: { insight: YTKeyInsight; index: number }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="rounded-lg border border-border bg-card/50 p-3 hover:bg-card/80 transition-colors">
      <button
        className="w-full text-left flex items-start gap-3"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-xs font-mono text-muted-foreground mt-0.5 shrink-0">
          {String(index + 1).padStart(2, '0')}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground leading-snug">{insight.insight}</p>
          {insight.timestamp_approx && (
            <span className="text-xs text-muted-foreground mt-1 inline-block">
              ~{insight.timestamp_approx}
            </span>
          )}
        </div>
        <span className="text-muted-foreground shrink-0">
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </span>
      </button>

      {expanded && (
        <div className="mt-3 ml-8 space-y-2 text-sm">
          {insight.quote && (
            <blockquote className="border-l-2 border-primary/40 pl-3 text-muted-foreground italic">
              "{insight.quote}"
            </blockquote>
          )}
          {insight.applicability && (
            <div className="flex items-start gap-2">
              <ArrowRight size={12} className="text-primary mt-1 shrink-0" />
              <p className="text-muted-foreground">{insight.applicability}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function OpportunityCard({
  opportunity,
  isTopPick,
  isSelected,
  onSelect,
}: {
  opportunity: YTAppOpportunity
  isTopPick: boolean
  isSelected: boolean
  onSelect: () => void
}) {
  const [expanded, setExpanded] = useState(isTopPick)

  return (
    <div
      className={`rounded-lg border transition-all ${
        isSelected
          ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
          : isTopPick
            ? 'border-primary/40 bg-primary/5'
            : 'border-border bg-card/50 hover:bg-card/80'
      }`}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Score circle */}
          <div
            className={`w-12 h-12 rounded-full border-2 flex items-center justify-center shrink-0 ${getScoreBg(opportunity.score)}`}
          >
            <span className={`text-lg font-bold ${getScoreColor(opportunity.score)}`}>
              {opportunity.score}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-sm font-semibold text-foreground">{opportunity.name}</h4>
              {isTopPick && (
                <Badge variant="outline" className="bg-primary/20 text-primary border-primary/30 gap-1">
                  <Trophy size={10} />
                  Top Pick
                </Badge>
              )}
              <Badge variant="outline" className={getTypeColor(opportunity.type)}>
                {opportunity.type}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{opportunity.one_liner}</p>

            {/* Quick stats row */}
            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Zap size={11} />
                {getComplexityLabel(opportunity.complexity)}
              </span>
              <span className={`font-medium ${getScoreColor(opportunity.score)}`}>
                {getScoreLabel(opportunity.score)}
              </span>
            </div>
          </div>

          <button
            className="text-muted-foreground hover:text-foreground p-1 shrink-0"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-border/50 pt-3">
          {/* Description */}
          <p className="text-sm text-muted-foreground">{opportunity.description}</p>

          {/* Why this works */}
          {opportunity.why_this_works && (
            <div className="rounded-md bg-green-500/5 border border-green-500/20 p-3">
              <div className="flex items-center gap-1.5 text-xs font-medium text-green-400 mb-1">
                <Star size={12} />
                Why This Works
              </div>
              <p className="text-sm text-muted-foreground">{opportunity.why_this_works}</p>
            </div>
          )}

          {/* Strategic Value */}
          {opportunity.strategic_value && (
            <div className="rounded-md bg-blue-500/5 border border-blue-500/20 p-3">
              <div className="flex items-center gap-1.5 text-xs font-medium text-blue-400 mb-1">
                <Target size={12} />
                Strategic Value
              </div>
              <p className="text-sm text-muted-foreground">{opportunity.strategic_value}</p>
            </div>
          )}

          {/* Concerns */}
          {opportunity.concerns && (
            <div className="rounded-md bg-orange-500/5 border border-orange-500/20 p-3">
              <div className="flex items-center gap-1.5 text-xs font-medium text-orange-400 mb-1">
                <AlertTriangle size={12} />
                Concerns
              </div>
              <p className="text-sm text-muted-foreground">{opportunity.concerns}</p>
            </div>
          )}

          {/* Core Features */}
          {opportunity.features.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground mb-2">
                Core Features
              </div>
              <div className="flex flex-wrap gap-1.5">
                {opportunity.features.map((f, i) => (
                  <Badge
                    key={i}
                    variant="outline"
                    className="bg-zinc-500/10 text-zinc-400 border-zinc-500/30"
                  >
                    {f}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Growth Path */}
          {opportunity.growth_path && (
            <div className="flex items-start gap-2 text-sm">
              <TrendingUp size={14} className="text-primary mt-0.5 shrink-0" />
              <div>
                <span className="text-xs font-medium text-muted-foreground">Growth Path: </span>
                <span className="text-muted-foreground">{opportunity.growth_path}</span>
              </div>
            </div>
          )}

          {/* Market Signal */}
          {opportunity.market_signal && (
            <p className="text-xs text-muted-foreground italic">
              Market signal: {opportunity.market_signal}
            </p>
          )}

          {/* Select button */}
          <Button
            variant={isSelected ? 'default' : 'outline'}
            size="sm"
            className="w-full gap-2 mt-2"
            onClick={onSelect}
          >
            {isSelected ? (
              <>
                <CheckCircle2 size={14} />
                Selected — Will Focus Strategy Extraction on This
              </>
            ) : (
              <>
                <Rocket size={14} />
                Select This Opportunity
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

interface DiscoveryPanelProps {
  ingestResult: YTIngestResponse
  onOpportunitySelected: (opportunity: YTAppOpportunity | null) => void
  selectedOpportunity: YTAppOpportunity | null
  /** Pre-populate the context field (e.g. from project description) */
  initialContext?: string
  /** Pre-loaded discovery result from localStorage persistence. */
  discoveryResult?: YTDiscoverResponse | null
  /** Called when discovery completes so parent can persist to localStorage. */
  onDiscoveryComplete?: (result: YTDiscoverResponse) => void
}

export function DiscoveryPanel({
  ingestResult,
  onOpportunitySelected,
  selectedOpportunity,
  initialContext,
  discoveryResult,
  onDiscoveryComplete,
}: DiscoveryPanelProps) {
  const [userContext, setUserContext] = useState(initialContext ?? '')
  const [model, setModel] = useState('claude-sonnet-4-6')
  const [isDiscovering, setIsDiscovering] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<YTDiscoverResponse | null>(discoveryResult ?? null)
  const [discoveryTime, setDiscoveryTime] = useState<number | null>(null)
  const [discoveryLogs, setDiscoveryLogs] = useState<Array<{ message: string; elapsed: number }>>([])
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const logEndRef = useRef<HTMLDivElement>(null)

  // Elapsed timer
  useEffect(() => {
    if (!isDiscovering) return
    setElapsedSeconds(0)
    const interval = setInterval(() => setElapsedSeconds(prev => prev + 1), 1000)
    return () => clearInterval(interval)
  }, [isDiscovering])

  // Auto-scroll log
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [discoveryLogs])

  const handleDiscover = useCallback(async () => {
    setIsDiscovering(true)
    setError(null)
    setDiscoveryTime(null)
    setDiscoveryLogs([])

    try {
      const response = await discoverOpportunitiesStream(
        {
          video_id: ingestResult.video_id,
          transcript: ingestResult.transcript,
          metadata: {
            title: ingestResult.title,
            channel: ingestResult.channel,
            duration: ingestResult.duration,
            description: ingestResult.description,
          },
          user_context: userContext,
          extracted_urls: ingestResult.extracted_urls,
          screenshot_suggestions: ingestResult.screenshot_suggestions,
          model,
        },
        (entry: DiscoveryLogEntry) => {
          if (entry.type === 'log' && entry.message) {
            setDiscoveryLogs(prev => [...prev, { message: entry.message!, elapsed: entry.elapsed }])
          }
        },
      )

      setResult(response)
      onDiscoveryComplete?.(response)
      setDiscoveryTime(response.discovery_time)

      // Auto-select the top pick
      if (response.app_opportunities.length > 0) {
        const topIdx = response.recommendation.top_pick_index
        const topPick = response.app_opportunities[topIdx] || response.app_opportunities[0]
        onOpportunitySelected(topPick)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Discovery failed')
    } finally {
      setIsDiscovering(false)
    }
  }, [ingestResult, userContext, model, onOpportunitySelected])

  const handleSelectOpportunity = useCallback(
    (opp: YTAppOpportunity) => {
      if (selectedOpportunity?.name === opp.name) {
        onOpportunitySelected(null)
      } else {
        onOpportunitySelected(opp)
      }
    },
    [selectedOpportunity, onOpportunitySelected],
  )

  return (
    <div className="rounded-lg border border-border bg-card">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Search size={18} className="text-primary" />
        <h3 className="text-sm font-semibold text-foreground">Discovery & Evaluation</h3>
        <span className="text-xs text-muted-foreground ml-1">Think before you build</span>
        {discoveryTime != null && (
          <span className="ml-auto text-xs text-muted-foreground">
            Analyzed in {discoveryTime.toFixed(1)}s
          </span>
        )}
      </div>

      <div className="p-4 space-y-4">
        {!result ? (
          /* Pre-discovery: context input + discover button */
          <>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                What are you looking for? (optional)
              </label>
              <Textarea
                value={userContext}
                onChange={(e) => setUserContext(e.target.value)}
                placeholder="e.g., I want to find app opportunities from this video — especially simple companion apps that could get users engaged quickly. I'm interested in consumer apps, not B2B."
                className="min-h-16 text-sm"
                disabled={isDiscovering}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Analysis Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                disabled={isDiscovering}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
              >
                <option value="claude-sonnet-4-6">Sonnet 4.6 (Recommended)</option>
                <option value="claude-opus-4-6">Opus 4.6 (Deeper analysis)</option>
                <option value="claude-haiku-4-5">Haiku 4.5 (Fast)</option>
              </select>
            </div>

            {error && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2">
                <AlertTriangle size={16} className="text-destructive shrink-0 mt-0.5" />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            <Button
              onClick={handleDiscover}
              disabled={isDiscovering || !ingestResult.transcript.length}
              className="w-full gap-2"
              variant="outline"
            >
              {isDiscovering ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Analyzing Video... {elapsedSeconds}s
                </>
              ) : (
                <>
                  <Lightbulb size={16} />
                  Discover Opportunities
                </>
              )}
            </Button>

            {/* Discovery processing log */}
            {(isDiscovering || discoveryLogs.length > 0) && discoveryLogs.length > 0 && (
              <div className="rounded-md border border-border bg-black/90 p-3 font-mono text-xs max-h-44 overflow-y-auto">
                {discoveryLogs.map((log, i) => (
                  <div key={i} className="flex gap-2 py-0.5">
                    <span className="text-emerald-400 shrink-0 tabular-nums">[{log.elapsed.toFixed(1)}s]</span>
                    <span className="text-gray-200">{log.message}</span>
                  </div>
                ))}
                {isDiscovering && (
                  <div className="flex gap-2 py-0.5">
                    <span className="text-emerald-400 shrink-0 tabular-nums">[{elapsedSeconds}.0s]</span>
                    <span className="text-yellow-300 animate-pulse">Waiting...</span>
                  </div>
                )}
                <div ref={logEndRef} />
              </div>
            )}

            <p className="text-xs text-muted-foreground text-center">
              AI will analyze the video to find key insights and app opportunities before you build anything.
            </p>
          </>
        ) : (
          /* Post-discovery: show results */
          <>
            {/* Video Context */}
            {result.video_context && (
              <div className="rounded-md bg-muted/30 border border-border p-3 space-y-1">
                {result.video_context.speaker && (
                  <p className="text-sm">
                    <span className="font-medium text-foreground">Speaker:</span>{' '}
                    <span className="text-muted-foreground">{result.video_context.speaker}</span>
                  </p>
                )}
                {result.video_context.core_topic && (
                  <p className="text-sm">
                    <span className="font-medium text-foreground">Topic:</span>{' '}
                    <span className="text-muted-foreground">{result.video_context.core_topic}</span>
                  </p>
                )}
                {result.video_context.target_audience && (
                  <p className="text-sm">
                    <span className="font-medium text-foreground">For:</span>{' '}
                    <span className="text-muted-foreground">{result.video_context.target_audience}</span>
                  </p>
                )}
              </div>
            )}

            {/* Key Insights */}
            {result.key_insights.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                  <Lightbulb size={12} />
                  Key Insights ({result.key_insights.length})
                </h4>
                <div className="space-y-1.5">
                  {result.key_insights.map((insight, i) => (
                    <InsightCard key={i} insight={insight} index={i} />
                  ))}
                </div>
              </div>
            )}

            {/* App Opportunities */}
            {result.app_opportunities.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                  <Rocket size={12} />
                  App Opportunities ({result.app_opportunities.length})
                </h4>
                <div className="space-y-3">
                  {result.app_opportunities.map((opp, i) => (
                    <OpportunityCard
                      key={i}
                      opportunity={opp}
                      isTopPick={i === result.recommendation.top_pick_index}
                      isSelected={selectedOpportunity?.name === opp.name}
                      onSelect={() => handleSelectOpportunity(opp)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Recommendation */}
            {result.recommendation && (
              <Card className="border-primary/30 bg-primary/5">
                <CardContent className="p-4 space-y-2">
                  <h4 className="text-xs font-medium text-primary uppercase tracking-wide flex items-center gap-1.5">
                    <Trophy size={12} />
                    Recommendation
                  </h4>
                  {result.recommendation.reasoning && (
                    <p className="text-sm text-muted-foreground">{result.recommendation.reasoning}</p>
                  )}
                  {result.recommendation.quick_win && (
                    <div className="flex items-start gap-2 text-sm">
                      <Zap size={14} className="text-yellow-400 mt-0.5 shrink-0" />
                      <div>
                        <span className="font-medium text-foreground">Quick Win: </span>
                        <span className="text-muted-foreground">{result.recommendation.quick_win}</span>
                      </div>
                    </div>
                  )}
                  {result.recommendation.sequence && (
                    <div className="flex items-start gap-2 text-sm">
                      <ArrowRight size={14} className="text-primary mt-0.5 shrink-0" />
                      <div>
                        <span className="font-medium text-foreground">Sequence: </span>
                        <span className="text-muted-foreground">{result.recommendation.sequence}</span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Re-discover button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setResult(null)
                setDiscoveryTime(null)
                onOpportunitySelected(null)
              }}
              className="w-full text-muted-foreground"
            >
              Re-analyze with different context
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
