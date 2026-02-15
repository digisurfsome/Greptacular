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
      <Badge className={`bg-amber-400 text-amber-950 border-amber-600 gap-1 ${className}`}>
        <Star size={12} />
        QA Verified
      </Badge>
    )
  }

  if (reviewed) {
    return (
      <Badge className={`bg-emerald-500 text-white border-emerald-700 gap-1 ${className}`}>
        <Shield size={12} />
        Reviewed
      </Badge>
    )
  }

  if (passes) {
    return (
      <Badge className={`bg-blue-500 text-white border-blue-700 gap-1 ${className}`}>
        <Check size={12} />
        Passing
      </Badge>
    )
  }

  return null
}
