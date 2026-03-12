/**
 * Entry point button for generating a tool from a YT Lab project.
 * Appears in the project detail view when steps exist.
 */

import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface GenerateToolButtonProps {
  projectId: string
  stepCount: number
  onClick: () => void
}

export function GenerateToolButton({ stepCount, onClick }: GenerateToolButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={stepCount === 0}
      className="gap-1.5"
      title={stepCount === 0 ? 'Add steps first' : 'Generate a Google Sheets tool from this strategy'}
    >
      <Sparkles size={16} />
      Generate Tool
    </Button>
  )
}
