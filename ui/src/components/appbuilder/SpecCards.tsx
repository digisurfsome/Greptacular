/**
 * SpecCards Component
 *
 * Grid of feature spec cards showing status.
 * Each card displays feature name, priority, complexity, and review status.
 */

import { FileText, Eye } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { AgentOSFeatureItem } from '@/hooks/useAgentOS'

// ============================================================================
// Types & Constants
// ============================================================================

interface SpecCardsProps {
  projectName: string
  features: AgentOSFeatureItem[]
  onReviewSpec: (featureId: number) => void
}

const PRIORITY_COLORS: Record<string, string> = {
  must_have: 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-300',
  should_have: 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-300',
  nice_to_have: 'bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-900/30 dark:text-gray-400',
}

const COMPLEXITY_COLORS: Record<string, string> = {
  small: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  large: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

// ============================================================================
// Component
// ============================================================================

export function SpecCards({ features, onReviewSpec }: SpecCardsProps) {
  if (features.length === 0) {
    return (
      <Card>
        <CardContent className="p-4 text-center">
          <FileText size={20} className="mx-auto text-muted-foreground mb-2" />
          <p className="text-xs text-muted-foreground">No features yet</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-2 px-1 mb-2">
        <FileText size={14} className="text-green-500" />
        <span className="text-xs font-bold text-foreground uppercase tracking-wider">
          Feature Specs ({features.length})
        </span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {features.map(feature => (
          <FeatureCard
            key={feature.id}
            feature={feature}
            onReview={() => onReviewSpec(feature.id)}
          />
        ))}
      </div>
    </div>
  )
}

// ============================================================================
// Card sub-component
// ============================================================================

function FeatureCard({
  feature,
  onReview,
}: {
  feature: AgentOSFeatureItem
  onReview: () => void
}) {
  const priorityLabel = feature.priority.replace(/_/g, ' ')

  return (
    <Card className="hover:border-primary/30 transition-colors">
      <CardContent className="p-3">
        {/* ID + Name */}
        <div className="flex items-start gap-1.5 mb-2">
          <span className="text-[10px] font-mono text-muted-foreground shrink-0">
            #{feature.id}
          </span>
          <span className="text-xs font-bold text-foreground leading-tight line-clamp-2">
            {feature.name}
          </span>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-1 mb-2">
          <Badge
            variant="outline"
            className={`text-[9px] capitalize ${PRIORITY_COLORS[feature.priority] || ''}`}
          >
            {priorityLabel}
          </Badge>
          <Badge
            variant="outline"
            className={`text-[9px] capitalize ${COMPLEXITY_COLORS[feature.complexity] || ''}`}
          >
            {feature.complexity}
          </Badge>
        </div>

        {/* Category */}
        {feature.category && (
          <span className="text-[10px] text-muted-foreground block mb-2">
            {feature.category}
          </span>
        )}

        {/* Review button */}
        <Button
          variant="ghost"
          size="sm"
          className="h-6 text-[10px] w-full"
          onClick={onReview}
        >
          <Eye size={10} />
          Review
        </Button>
      </CardContent>
    </Card>
  )
}
