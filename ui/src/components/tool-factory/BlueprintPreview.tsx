/**
 * Full blueprint review screen. Shows the chain as a vertical flow
 * with step cards, type badges, prompts, and detected APIs.
 */

import { useState, useCallback } from 'react'
import { ArrowLeft, ArrowDown, Check, Pencil, X, Key, Zap, ChevronDown, ChevronRight, AlertTriangle, ExternalLink, DollarSign, Clock, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import type { TFSheetBlueprint, TFChainConfigRow, TFStepType, TFAPIResearchResult, TFBlueprintAPIResearch } from '@/lib/types'

interface BlueprintPreviewProps {
  blueprint: TFSheetBlueprint
  onConfirm: (blueprint: TFSheetBlueprint) => void
  onBack: () => void
}

function getStepTypeColor(type: TFStepType): string {
  switch (type) {
    case 'research': return 'bg-blue-500/10 text-blue-600 border-blue-500/30'
    case 'generation': return 'bg-purple-500/10 text-purple-600 border-purple-500/30'
    case 'action': return 'bg-orange-500/10 text-orange-600 border-orange-500/30'
    case 'manual': return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/30'
  }
}

function StepCard({
  step,
  onUpdatePrompt,
}: {
  step: TFChainConfigRow
  onUpdatePrompt: (prompt: string) => void
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(step.prompt_template)

  const handleSave = useCallback(() => {
    onUpdatePrompt(editValue)
    setIsEditing(false)
  }, [editValue, onUpdatePrompt])

  return (
    <Card className="border-2">
      <CardContent className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-muted-foreground">#{step.row_number}</span>
            <Badge variant="outline" className={getStepTypeColor(step.step_type)}>
              {step.step_type}
            </Badge>
            <h3 className="text-sm font-semibold text-foreground">{step.title}</h3>
          </div>
          {step.is_gate && (
            <Badge className="bg-amber-500/10 text-amber-600 border-amber-500/30 shrink-0">
              Gate
            </Badge>
          )}
        </div>

        {/* Prompt */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Prompt</span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2"
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? <X size={12} /> : <Pencil size={12} />}
            </Button>
          </div>
          {isEditing ? (
            <div className="space-y-2">
              <Textarea
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="font-mono text-xs min-h-[80px]"
              />
              <div className="flex gap-2">
                <Button size="sm" className="h-7" onClick={handleSave}>
                  <Check size={12} className="mr-1" /> Save
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7"
                  onClick={() => { setEditValue(step.prompt_template); setIsEditing(false) }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground font-mono whitespace-pre-wrap line-clamp-3">
              {step.prompt_template}
            </p>
          )}
        </div>

        {/* I/O and metadata */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <span>In: <span className="text-foreground">{step.input_source || 'User input'}</span></span>
          <span>Out: <span className="text-foreground">{step.output_destination || 'Next step'}</span></span>
          <span>Model: <span className="text-foreground">{step.model_recommendation}</span></span>
        </div>

        {/* APIs */}
        {step.apis_required.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <Key size={12} className="text-muted-foreground" />
            {step.apis_required.map((api) => (
              <Badge key={api} variant="outline" className="text-xs">
                {api}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Collapsible card for a single API research result showing pricing,
 * red flags, and cheaper alternatives. Expanded by default when red
 * flags exist so the user sees warnings immediately.
 */
function APIResearchCard({ result }: { result: TFAPIResearchResult }) {
  const hasRedFlags = result.red_flags.length > 0
  const [isExpanded, setIsExpanded] = useState(hasRedFlags)

  const isStatic = result.research_source === 'static_database'
  const isNotFound = result.research_source === 'not_found'

  return (
    <div className="border-2 border-border rounded-lg overflow-hidden">
      {/* Clickable header */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <Search size={14} className="text-muted-foreground shrink-0" />
          <span className="text-sm font-semibold text-foreground">{result.service_name}</span>
          <Badge variant="outline" className="text-xs">
            {result.category}
          </Badge>
          {hasRedFlags && (
            <Badge className="bg-orange-500/10 text-orange-600 border-orange-500/30 text-xs">
              <AlertTriangle size={10} className="mr-0.5" />
              {result.red_flags.length} warning{result.red_flags.length > 1 ? 's' : ''}
            </Badge>
          )}
          {isStatic && (
            <Badge variant="outline" className="text-xs text-muted-foreground">
              <Clock size={10} className="mr-0.5" />
              Cached
            </Badge>
          )}
        </div>
        {isExpanded
          ? <ChevronDown size={16} className="text-muted-foreground shrink-0" />
          : <ChevronRight size={16} className="text-muted-foreground shrink-0" />
        }
      </button>

      {/* Expanded detail body */}
      {isExpanded && (
        <div className="border-t border-border p-4 space-y-4">
          {/* Pricing details */}
          <div className="space-y-1.5">
            <p className="text-sm text-foreground">
              <span className="font-medium">Pricing:</span>{' '}
              {result.pricing_summary}
            </p>
            <p className="text-sm text-foreground">
              <span className="font-medium">API Access:</span>{' '}
              <span className={
                result.api_access_cost.toLowerCase().includes('free')
                  ? 'text-green-600'
                  : 'text-orange-600 font-medium'
              }>
                {result.api_access_cost}
              </span>
            </p>
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Per-use:</span>{' '}
              {result.per_unit_cost}
            </p>
          </div>

          {/* Pricing tiers (if available) */}
          {result.pricing_tiers.length > 0 && (
            <div className="space-y-1">
              <span className="text-xs font-medium text-muted-foreground">Pricing Tiers</span>
              <ul className="text-xs text-muted-foreground space-y-0.5 list-disc list-inside">
                {result.pricing_tiers.map((tier, i) => (
                  <li key={i}>{tier}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Red flags */}
          {hasRedFlags && (
            <div className="space-y-1.5">
              <span className="text-xs font-medium text-orange-600 flex items-center gap-1">
                <AlertTriangle size={12} />
                Red Flags
              </span>
              <ul className="space-y-1">
                {result.red_flags.map((flag, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-orange-700">
                    <span className="text-orange-500 mt-0.5 shrink-0">&#x2022;</span>
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Alternatives table */}
          {result.alternatives.length > 0 ? (
            <div className="space-y-1.5">
              <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <DollarSign size={12} />
                Cheaper Alternatives
              </span>
              <div className="border border-border rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-muted/50">
                      <th className="text-left p-2 font-medium text-muted-foreground">Service</th>
                      <th className="text-left p-2 font-medium text-muted-foreground">Price</th>
                      <th className="text-left p-2 font-medium text-muted-foreground hidden sm:table-cell">Tradeoff</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.alternatives.map((alt) => (
                      <tr key={alt.service_name} className="border-t border-border">
                        <td className="p-2">
                          <div className="flex flex-col gap-0.5">
                            <span className="font-medium text-foreground">{alt.service_name}</span>
                            {alt.free_tier.toLowerCase().startsWith('yes') && (
                              <span className="text-green-600 text-[10px]">Free tier available</span>
                            )}
                          </div>
                        </td>
                        <td className="p-2 text-muted-foreground">{alt.monthly_cost}</td>
                        <td className="p-2 text-muted-foreground hidden sm:table-cell">{alt.tradeoff}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground italic">No alternatives found</p>
          )}

          {/* Static data disclaimer */}
          {isStatic && (
            <p className="text-[10px] text-muted-foreground italic">
              Cached data -- may not reflect current pricing
            </p>
          )}
          {isNotFound && (
            <p className="text-[10px] text-orange-600 italic">
              Pricing data could not be retrieved -- verify manually
            </p>
          )}

          {/* Action buttons: signup links for main service + alternatives */}
          <div className="flex flex-wrap gap-2">
            {result.alternatives.map((alt) => (
              alt.signup_url && (
                <a
                  key={alt.service_name}
                  href={alt.signup_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                >
                  <ExternalLink size={10} />
                  Try {alt.service_name}
                </a>
              )
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * API Cost Analysis section for the blueprint preview.
 * Shows a collapsible card per API with pricing, alternatives, and red flags.
 * Returns null if no research data is available, hiding the section entirely.
 */
function APICostAnalysis({ research }: { research: TFBlueprintAPIResearch }) {
  const [isSectionExpanded, setIsSectionExpanded] = useState(true)
  const totalRedFlags = research.results.reduce(
    (sum, r) => sum + r.red_flags.length, 0
  )

  // Determine the primary research source for the badge label
  const hasWebResearch = research.results.some(
    (r) => r.research_source === 'web_research'
  )
  const researchLabel = hasWebResearch ? 'Live research' : 'Cached data'

  return (
    <Card className="mt-6 border-2">
      <CardContent className="p-4 space-y-4">
        {/* Section header */}
        <button
          type="button"
          onClick={() => setIsSectionExpanded(!isSectionExpanded)}
          className="w-full flex items-center justify-between"
        >
          <div className="flex items-center gap-2 flex-wrap">
            <DollarSign size={16} className="text-foreground" />
            <h3 className="text-sm font-semibold text-foreground">API Cost Analysis</h3>
            <Badge variant="outline" className="text-xs">
              {research.results.length} API{research.results.length !== 1 ? 's' : ''}
            </Badge>
            {totalRedFlags > 0 && (
              <Badge className="bg-orange-500/10 text-orange-600 border-orange-500/30 text-xs">
                <AlertTriangle size={10} />
                {totalRedFlags} warning{totalRedFlags !== 1 ? 's' : ''}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs text-muted-foreground">
              {researchLabel}
            </Badge>
            {isSectionExpanded
              ? <ChevronDown size={14} className="text-muted-foreground" />
              : <ChevronRight size={14} className="text-muted-foreground" />
            }
          </div>
        </button>

        {isSectionExpanded && (
          <div className="space-y-4">
            {/* Total cost summary */}
            <div className="bg-muted/50 rounded-lg p-3">
              <p className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">Estimated monthly cost: </span>
                {research.total_estimated_monthly_cost}
              </p>
              {research.research_duration_seconds > 0 && (
                <p className="text-[10px] text-muted-foreground mt-1">
                  Research completed in {research.research_duration_seconds.toFixed(1)}s
                </p>
              )}
            </div>

            {/* Individual API cards */}
            <div className="space-y-2">
              {research.results.map((result) => (
                <APIResearchCard key={result.service_key} result={result} />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function BlueprintPreview({ blueprint, onConfirm, onBack }: BlueprintPreviewProps) {
  const [editedBlueprint, setEditedBlueprint] = useState(blueprint)

  const handleUpdatePrompt = useCallback((rowNumber: number, prompt: string) => {
    setEditedBlueprint((prev) => ({
      ...prev,
      chain_config: prev.chain_config.map((row) =>
        row.row_number === rowNumber ? { ...row, prompt_template: prompt } : row
      ),
    }))
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-center h-12 px-4 border-b border-border bg-card shrink-0">
        <Button variant="ghost" size="sm" onClick={onBack} className="gap-1.5 mr-4">
          <ArrowLeft size={14} />
          Back
        </Button>
        <div className="flex-1">
          <h2 className="text-sm font-semibold text-foreground">{editedBlueprint.tool_name}</h2>
          <p className="text-xs text-muted-foreground">{editedBlueprint.tool_description}</p>
        </div>
        <Button onClick={() => onConfirm(editedBlueprint)} className="gap-1.5">
          <Zap size={14} />
          Deploy
        </Button>
      </div>

      {/* Chain flow */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-2">
          {/* Summary */}
          <div className="flex flex-wrap gap-3 mb-6 text-sm text-muted-foreground">
            <span>{editedBlueprint.chain_config.length} steps</span>
            <span>{editedBlueprint.detected_apis.length} APIs</span>
            <span>{editedBlueprint.user_input_variables.length} variables</span>
            <span className="capitalize">Source: {editedBlueprint.ingestion_source.replace('_', ' ')}</span>
          </div>

          {editedBlueprint.chain_config.map((step, i) => (
            <div key={step.row_number}>
              <StepCard
                step={step}
                onUpdatePrompt={(prompt) => handleUpdatePrompt(step.row_number, prompt)}
              />
              {i < editedBlueprint.chain_config.length - 1 && (
                <div className="flex justify-center py-1">
                  <ArrowDown size={16} className="text-muted-foreground/40" />
                </div>
              )}
            </div>
          ))}

          {/* API Cost Analysis — only rendered when research data is available */}
          {editedBlueprint.api_research && editedBlueprint.api_research.results.length > 0 && (
            <APICostAnalysis research={editedBlueprint.api_research} />
          )}

          {/* Detected APIs summary */}
          {editedBlueprint.detected_apis.length > 0 && (
            <Card className="mt-6 border-2">
              <CardContent className="p-4">
                <h3 className="text-sm font-semibold text-foreground mb-3">Required APIs</h3>
                <div className="space-y-2">
                  {editedBlueprint.detected_apis.map((api) => (
                    <div key={api.service_key} className="flex items-center justify-between text-sm">
                      <span className="text-foreground">{api.service_name}</span>
                      <a
                        href={api.signup_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline"
                      >
                        Get API key
                      </a>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
