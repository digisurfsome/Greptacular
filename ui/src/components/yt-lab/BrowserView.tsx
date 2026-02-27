/**
 * BrowserView — noVNC iframe wrapper for the execution viewer.
 *
 * Embeds a noVNC WebSocket connection in an iframe to show the agent's
 * browser in real-time. Supports view-only (default) and interactive
 * (takeover) modes. Maintains display aspect ratio with letterboxing.
 */

import { useState } from 'react'
import { Monitor, Loader2, WifiOff } from 'lucide-react'
import type { YTExecutionStatus } from '@/lib/types'

interface BrowserViewProps {
  novncUrl: string | null
  status: YTExecutionStatus
  isTakeover: boolean
}

export function BrowserView({ novncUrl, status, isTakeover }: BrowserViewProps) {
  const [iframeLoaded, setIframeLoaded] = useState(false)

  // Build the noVNC URL with view-only parameter
  const buildIframeUrl = (): string | null => {
    if (!novncUrl) return null
    try {
      const url = new URL(novncUrl)
      url.searchParams.set('autoconnect', 'true')
      url.searchParams.set('resize', 'scale')
      if (!isTakeover) {
        url.searchParams.set('view_only', 'true')
      }
      return url.toString()
    } catch {
      // If not a valid URL, use as-is with query params
      const separator = novncUrl.includes('?') ? '&' : '?'
      const viewOnly = isTakeover ? '' : '&view_only=true'
      return `${novncUrl}${separator}autoconnect=true&resize=scale${viewOnly}`
    }
  }

  const iframeUrl = buildIframeUrl()

  // Status-specific overlays
  if (status === 'idle') {
    return (
      <div className="flex-1 flex items-center justify-center bg-black/90 rounded-lg">
        <div className="text-center">
          <Monitor className="w-16 h-16 text-muted-foreground/30 mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">Ready to start execution</p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Click Run to begin the agent session
          </p>
        </div>
      </div>
    )
  }

  if (status === 'completed') {
    return (
      <div className="flex-1 flex items-center justify-center bg-black/90 rounded-lg">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-3">
            <span className="text-2xl">&#10003;</span>
          </div>
          <p className="text-sm text-green-400 font-medium">Execution Complete</p>
          <p className="text-xs text-muted-foreground mt-1">
            All steps have been executed
          </p>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="flex-1 flex items-center justify-center bg-black/90 rounded-lg">
        <div className="text-center">
          <WifiOff className="w-16 h-16 text-red-400/50 mx-auto mb-3" />
          <p className="text-sm text-red-400 font-medium">Execution Error</p>
          <p className="text-xs text-muted-foreground mt-1">
            Check the agent log for details
          </p>
        </div>
      </div>
    )
  }

  if (!iframeUrl) {
    return (
      <div className="flex-1 flex items-center justify-center bg-black/90 rounded-lg">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">Connecting to browser...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 relative bg-black rounded-lg overflow-hidden">
      {/* Takeover mode indicator */}
      {isTakeover && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 z-10 px-3 py-1 bg-amber-500/90 text-black text-xs font-bold rounded-full shadow-lg">
          YOU ARE IN CONTROL
        </div>
      )}

      {/* Paused overlay */}
      {status === 'paused' && !isTakeover && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/40">
          <div className="px-4 py-2 bg-card/90 border border-border rounded-lg shadow-lg">
            <p className="text-sm font-medium text-foreground animate-pulse">Paused</p>
          </div>
        </div>
      )}

      {/* Loading indicator (before iframe loads) */}
      {!iframeLoaded && (
        <div className="absolute inset-0 flex items-center justify-center z-5">
          <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
        </div>
      )}

      {/* noVNC iframe */}
      <iframe
        src={iframeUrl}
        title="Agent Browser View"
        className="w-full h-full border-0"
        onLoad={() => setIframeLoaded(true)}
        sandbox="allow-scripts allow-same-origin allow-popups"
        style={{ aspectRatio: '16 / 9' }}
      />
    </div>
  )
}
