/**
 * StyleFullPreview Component
 *
 * Full-screen overlay that shows a complete mock app layout rendered in a
 * specific design style. Triggered by hovering/clicking a style card in the
 * grid. Includes a "Select This Style" button.
 */

import { X } from 'lucide-react'
import { StylePreview } from './StylePreview'
import { Button } from '@/components/ui/button'
import type { StyleGuide } from '../lib/types'

interface StyleFullPreviewProps {
  guide: StyleGuide
  styleName: string
  styleDescription: string
  onSelect: () => void
  onClose: () => void
}

export function StyleFullPreview({
  guide,
  styleName,
  styleDescription,
  onSelect,
  onClose,
}: StyleFullPreviewProps) {
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Content */}
      <div
        className="relative z-10 w-[90vw] h-[85vh] max-w-6xl rounded-xl overflow-hidden border border-border bg-background shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header bar */}
        <div className="flex items-center justify-between px-6 py-3 border-b bg-background/95 backdrop-blur shrink-0">
          <div>
            <h2 className="text-lg font-semibold">{styleName}</h2>
            <p className="text-sm text-muted-foreground">{styleDescription}</p>
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={onSelect}>
              Select This Style
            </Button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Preview area */}
        <div className="flex-1 overflow-y-auto">
          <StylePreview guide={guide} size="full" styleName={styleName} />
        </div>
      </div>
    </div>
  )
}
