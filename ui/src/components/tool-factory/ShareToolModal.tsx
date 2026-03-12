/**
 * Modal for sharing a tool -- copy URL, export blueprint JSON, copy embed code.
 */

import { useState, useCallback } from 'react'
import { Copy, Check, Code, FileJson, Link } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import type { TFGeneratedTool } from '@/lib/types'

interface ShareToolModalProps {
  isOpen: boolean
  tool: TFGeneratedTool
  onClose: () => void
}

export function ShareToolModal({ isOpen, tool, onClose }: ShareToolModalProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const copyToClipboard = useCallback(async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedField(field)
      setTimeout(() => setCopiedField(null), 2000)
    } catch {
      // Clipboard not available
    }
  }, [])

  const embedCode = tool.sheet_url
    ? `<iframe src="${tool.sheet_url}?widget=true&headers=false" width="100%" height="400" frameborder="0"></iframe>`
    : ''

  const blueprintJson = JSON.stringify(tool.blueprint, null, 2)

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Share Tool</DialogTitle>
          <DialogDescription>
            Share or export &ldquo;{tool.blueprint.tool_name}&rdquo;
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Sheet URL */}
          {tool.sheet_url && (
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <Link size={12} /> Sheet URL
              </label>
              <div className="flex gap-2">
                <input
                  readOnly
                  value={tool.sheet_url}
                  className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm font-mono truncate"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(tool.sheet_url!, 'url')}
                >
                  {copiedField === 'url' ? <Check size={14} /> : <Copy size={14} />}
                </Button>
              </div>
            </div>
          )}

          {/* Embed code */}
          {tool.sheet_url && (
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <Code size={12} /> Embed Code
              </label>
              <div className="flex gap-2">
                <input
                  readOnly
                  value={embedCode}
                  className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm font-mono truncate"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(embedCode, 'embed')}
                >
                  {copiedField === 'embed' ? <Check size={14} /> : <Copy size={14} />}
                </Button>
              </div>
            </div>
          )}

          {/* Export JSON */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
              <FileJson size={12} /> Blueprint JSON
            </label>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 w-full"
              onClick={() => copyToClipboard(blueprintJson, 'json')}
            >
              {copiedField === 'json' ? <Check size={14} /> : <Copy size={14} />}
              {copiedField === 'json' ? 'Copied!' : 'Copy Blueprint JSON'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
