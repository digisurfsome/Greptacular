/**
 * Button that opens the PRD upload modal for direct PRD-to-tool generation.
 */

import { FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface PRDUploadButtonProps {
  onClick: () => void
}

export function PRDUploadButton({ onClick }: PRDUploadButtonProps) {
  return (
    <Button
      variant="outline"
      onClick={onClick}
      className="gap-1.5"
      title="Generate a tool from a PRD document"
    >
      <FileText size={16} />
      From PRD
    </Button>
  )
}
