import { Check, Shield, Star } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface PipelineStatusBadgeProps {
  passes: boolean
  reviewed?: boolean
  qa_verified?: boolean
  className?: string
}

export function PipelineStatusBadge({ passes, reviewed, qa_verified, className = '' }: PipelineStatusBadgeProps) {
  if (qa_verified) {
    return (
      <Badge
        className={`gap-1 ${className}`}
        style={{
          backgroundColor: 'var(--color-pipeline-qa-verified)',
          color: 'var(--color-pipeline-qa-verified-fg)',
          borderColor: 'var(--color-pipeline-qa-verified-border)',
        }}
      >
        <Star size={12} />
        QA Verified
      </Badge>
    )
  }

  if (reviewed) {
    return (
      <Badge
        className={`gap-1 ${className}`}
        style={{
          backgroundColor: 'var(--color-pipeline-reviewed)',
          color: 'var(--color-pipeline-reviewed-fg)',
          borderColor: 'var(--color-pipeline-reviewed-border)',
        }}
      >
        <Shield size={12} />
        Reviewed
      </Badge>
    )
  }

  if (passes) {
    return (
      <Badge
        className={`gap-1 ${className}`}
        style={{
          backgroundColor: 'var(--color-pipeline-passing)',
          color: 'var(--color-pipeline-passing-fg)',
          borderColor: 'var(--color-pipeline-passing-border)',
        }}
      >
        <Check size={12} />
        Passing
      </Badge>
    )
  }

  return null
}
