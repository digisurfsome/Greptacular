/**
 * Full blueprint review screen. Shows the chain as a vertical flow
 * with step cards, type badges, prompts, and detected APIs.
 */

import { useState, useCallback } from 'react'
import { ArrowLeft, ArrowDown, Check, Pencil, X, Key, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import type { TFSheetBlueprint, TFChainConfigRow, TFStepType } from '@/lib/types'

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
