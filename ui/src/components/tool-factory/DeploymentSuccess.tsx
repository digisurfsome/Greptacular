/**
 * Success screen after deploying a tool. Shows link to sheet, copy button,
 * and options to generate another or go to Tool Manager.
 */

import { CheckCircle2, Copy, ExternalLink, ArrowRight } from 'lucide-react'
import { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface DeploymentSuccessProps {
  sheetUrl: string
  sheetTitle: string
  toolId: string
  onGenerateAnother: () => void
  onGoToToolManager: () => void
}

export function DeploymentSuccess({
  sheetUrl,
  sheetTitle,
  toolId,
  onGenerateAnother,
  onGoToToolManager,
}: DeploymentSuccessProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(sheetUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard API not available
    }
  }, [sheetUrl])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm">
      <Card className="w-full max-w-md mx-4 border-2">
        <CardContent className="p-8 text-center space-y-6">
          {/* Success icon */}
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-full bg-[var(--color-neo-done)]/10 flex items-center justify-center">
              <CheckCircle2 size={32} className="text-[var(--color-neo-done)]" />
            </div>
          </div>

          <div>
            <h2 className="text-xl font-semibold text-foreground">Tool Deployed!</h2>
            <p className="text-sm text-muted-foreground mt-1">{sheetTitle}</p>
          </div>

          {/* Sheet link */}
          <div className="space-y-2">
            <a
              href={sheetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-primary hover:underline text-sm font-medium"
            >
              <ExternalLink size={14} />
              Open in Google Sheets
            </a>

            <div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
                className="gap-1.5"
              >
                <Copy size={14} />
                {copied ? 'Copied!' : 'Copy Link'}
              </Button>
            </div>
          </div>

          {/* Tool ID for reference */}
          <p className="text-xs text-muted-foreground font-mono">
            Tool ID: {toolId}
          </p>

          {/* Actions */}
          <div className="flex flex-col gap-2">
            <Button onClick={onGenerateAnother} variant="outline" className="gap-1.5">
              Generate Another
            </Button>
            <Button onClick={onGoToToolManager} className="gap-1.5">
              Go to Tool Manager
              <ArrowRight size={14} />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
