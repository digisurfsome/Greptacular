/**
 * DunkStack Live Preview Panel
 *
 * Embeds an iframe pointing at the project's dev server so the user
 * can see the running frontend in real-time during development without
 * needing to merge to main and rebuild.
 *
 * - Start/stop dev server inline
 * - Auto-detects URL from dev server output
 * - Responsive viewport toggles (desktop / tablet / mobile)
 * - Refresh and open-in-new-tab buttons
 * - Polls dev server status while panel is open
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Globe,
  RefreshCw,
  ExternalLink,
  Play,
  Square,
  Loader2,
  MonitorSmartphone,
  Smartphone,
  Monitor,
  AlertTriangle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  getDevServerStatus,
  startDevServer,
  stopDevServer,
} from '@/lib/api'
import type { DevServerStatus } from '@/lib/types'

interface DunkStackPreviewPanelProps {
  /** Currently selected project name */
  projectName: string
}

type ViewportMode = 'full' | 'tablet' | 'mobile'

const VIEWPORT_WIDTHS: Record<ViewportMode, string> = {
  full: '100%',
  tablet: '768px',
  mobile: '375px',
}

export function DunkStackPreviewPanel({ projectName }: DunkStackPreviewPanelProps): React.JSX.Element {
  const [status, setStatus] = useState<DevServerStatus>('stopped')
  const [url, setUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [starting, setStarting] = useState(false)
  const [stopping, setStopping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [viewport, setViewport] = useState<ViewportMode>('full')
  const [iframeKey, setIframeKey] = useState(0)
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Fetch dev server status
  const fetchStatus = useCallback(async () => {
    try {
      const data = await getDevServerStatus(projectName)
      setStatus(data.status)
      setUrl(data.url)
      setError(null)
    } catch (e) {
      // Server may not be running - don't overwrite existing state
      console.debug('Dev server status check failed:', e)
    }
  }, [projectName])

  // Initial fetch + polling every 3s while panel is open
  useEffect(() => {
    setLoading(true)
    fetchStatus().finally(() => setLoading(false))

    pollRef.current = setInterval(fetchStatus, 3000)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [fetchStatus])

  // Reset state when project changes
  useEffect(() => {
    setStatus('stopped')
    setUrl(null)
    setError(null)
    setIframeKey(prev => prev + 1)
  }, [projectName])

  const handleStart = async () => {
    setStarting(true)
    setError(null)
    try {
      await startDevServer(projectName)
      // Poll more aggressively for URL detection
      let attempts = 0
      const fastPoll = setInterval(async () => {
        attempts++
        try {
          const data = await getDevServerStatus(projectName)
          setStatus(data.status)
          if (data.url) {
            setUrl(data.url)
            setIframeKey(prev => prev + 1)
            clearInterval(fastPoll)
          }
          if (data.status === 'crashed') {
            clearInterval(fastPoll)
          }
        } catch { /* ignore */ }
        if (attempts >= 20) clearInterval(fastPoll) // Stop after ~20s
      }, 1000)
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e))
    } finally {
      setStarting(false)
    }
  }

  const handleStop = async () => {
    setStopping(true)
    setError(null)
    try {
      await stopDevServer(projectName)
      setStatus('stopped')
      setUrl(null)
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e))
    } finally {
      setStopping(false)
    }
  }

  const handleRefresh = () => {
    setIframeKey(prev => prev + 1)
  }

  const isRunning = status === 'running'
  const isCrashed = status === 'crashed'
  const hasUrl = isRunning && url

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <PreviewHeader viewport={viewport} onViewportChange={setViewport} />
        <div className="flex-1 flex items-center justify-center">
          <Loader2 size={24} className="animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <PreviewHeader viewport={viewport} onViewportChange={setViewport} />

      {/* Controls bar */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border/50 shrink-0">
        {!isRunning ? (
          <Button
            variant={isCrashed ? 'destructive' : 'outline'}
            size="sm"
            className="gap-1.5 text-xs h-7"
            onClick={handleStart}
            disabled={starting}
          >
            {starting ? (
              <Loader2 size={13} className="animate-spin" />
            ) : isCrashed ? (
              <AlertTriangle size={13} />
            ) : (
              <Play size={13} />
            )}
            {starting ? 'Starting...' : isCrashed ? 'Restart Server' : 'Start Dev Server'}
          </Button>
        ) : (
          <>
            <Button
              variant="destructive"
              size="sm"
              className="gap-1.5 text-xs h-7"
              onClick={handleStop}
              disabled={stopping}
            >
              {stopping ? <Loader2 size={13} className="animate-spin" /> : <Square size={13} />}
              Stop
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0"
              onClick={handleRefresh}
              title="Refresh preview"
            >
              <RefreshCw size={13} />
            </Button>

            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[10px] text-primary hover:underline font-mono"
                title={`Open ${url} in new tab`}
              >
                {url}
                <ExternalLink size={10} />
              </a>
            )}
          </>
        )}

        {error && (
          <span className="text-[10px] text-red-400 font-mono truncate ml-2">{error}</span>
        )}
      </div>

      {/* Preview area */}
      <div className="flex-1 overflow-hidden bg-zinc-900/50 flex items-center justify-center min-h-0">
        {hasUrl ? (
          <div
            className="h-full transition-all duration-200"
            style={{ width: VIEWPORT_WIDTHS[viewport], maxWidth: '100%' }}
          >
            <iframe
              ref={iframeRef}
              key={iframeKey}
              src={url}
              className="w-full h-full border-0 bg-white"
              title="Live Preview"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center gap-3 text-center px-4">
            <Globe size={40} className="text-muted-foreground/20" />
            <div>
              <p className="text-sm text-muted-foreground">
                {isRunning ? 'Waiting for URL detection...' : 'Dev server not running'}
              </p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                {isRunning
                  ? 'The server is starting up. The preview will appear once the URL is detected.'
                  : 'Start the dev server to see a live preview of your frontend.'}
              </p>
            </div>
            {isRunning && (
              <Loader2 size={16} className="animate-spin text-muted-foreground/40" />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================================
// Sub-components
// ============================================================================

function PreviewHeader({
  viewport,
  onViewportChange,
}: {
  viewport: ViewportMode
  onViewportChange: (v: ViewportMode) => void
}) {
  return (
    <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-card shrink-0">
      <div className="flex items-center gap-2">
        <Globe size={14} className="text-primary" />
        <span className="text-xs font-semibold text-foreground">Live Preview</span>
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onViewportChange('full')}
          className={`p-1 rounded transition-colors ${
            viewport === 'full' ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground'
          }`}
          title="Desktop view"
        >
          <Monitor size={13} />
        </button>
        <button
          onClick={() => onViewportChange('tablet')}
          className={`p-1 rounded transition-colors ${
            viewport === 'tablet' ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground'
          }`}
          title="Tablet view (768px)"
        >
          <MonitorSmartphone size={13} />
        </button>
        <button
          onClick={() => onViewportChange('mobile')}
          className={`p-1 rounded transition-colors ${
            viewport === 'mobile' ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground'
          }`}
          title="Mobile view (375px)"
        >
          <Smartphone size={13} />
        </button>
      </div>
    </div>
  )
}
