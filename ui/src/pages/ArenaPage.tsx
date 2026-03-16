/**
 * ArenaPage - Side-by-side AI model comparison.
 *
 * Renders 2 or 3 iframes, each loading ArenaChatPage with its own WebSocket
 * session. The parent broadcasts a single user question to all panels via
 * postMessage. Each panel independently sends it to its configured model.
 *
 * The parent page has ZERO WebSocket connections — only the iframes do.
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import { useWorkspaceProviders } from '../hooks/useWorkspaceConversations'
import { ArrowLeft, Send, Columns2, Columns3 } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface PanelConfig {
  id: string
  model: string
  provider: string
  status: 'idle' | 'streaming' | 'done' | 'error' | 'connected' | 'disconnected'
}

/** Flatten providers into a flat list of { provider, modelId, modelName }. */
function flattenModels(
  providers: Record<string, { name: string; models: { id: string; name: string }[] }> | undefined
): { provider: string; providerName: string; modelId: string; modelName: string }[] {
  if (!providers) return []
  const result: { provider: string; providerName: string; modelId: string; modelName: string }[] = []
  for (const [key, prov] of Object.entries(providers)) {
    for (const model of prov.models) {
      result.push({ provider: key, providerName: prov.name, modelId: model.id, modelName: model.name })
    }
  }
  return result
}

function getDefaultPanels(
  count: 2 | 3,
  models: ReturnType<typeof flattenModels>,
): PanelConfig[] {
  // Try to pick distinct models for each panel
  const defaults = ['claude-opus-4-6', 'claude-sonnet-4-6', 'codex']
  const panels: PanelConfig[] = []

  for (let i = 0; i < count; i++) {
    const preferred = defaults[i]
    const match = models.find((m) => m.modelId === preferred) || models[i] || models[0]
    panels.push({
      id: `panel-${i}`,
      model: match?.modelId || '',
      provider: match?.provider || 'claude',
      status: 'idle',
    })
  }
  return panels
}

export function ArenaPage(): React.JSX.Element {
  const { data: providers, isLoading: providersLoading } = useWorkspaceProviders()
  const allModels = flattenModels(providers)

  const [panelCount, setPanelCount] = useState<2 | 3>(3)
  const [panels, setPanels] = useState<PanelConfig[]>([])
  const [input, setInput] = useState('')
  const [hasSubmitted, setHasSubmitted] = useState(false)
  const iframeRefs = useRef<(HTMLIFrameElement | null)[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  // Initialize panels when providers load
  useEffect(() => {
    if (allModels.length > 0 && panels.length === 0) {
      setPanels(getDefaultPanels(panelCount, allModels))
    }
  }, [allModels.length, panelCount, panels.length])

  // Adjust panel count
  const togglePanelCount = useCallback(() => {
    const next = panelCount === 3 ? 2 : 3
    setPanelCount(next)
    setPanels((prev) => {
      if (next > prev.length) {
        // Add a panel
        const extra = allModels.find(
          (m) => !prev.some((p) => p.model === m.modelId && p.provider === m.provider)
        ) || allModels[0]
        return [
          ...prev,
          {
            id: `panel-${prev.length}`,
            model: extra?.modelId || '',
            provider: extra?.provider || 'claude',
            status: 'idle' as const,
          },
        ]
      }
      return prev.slice(0, next)
    })
  }, [panelCount, allModels])

  const updatePanelModel = useCallback(
    (panelIndex: number, modelId: string) => {
      const match = allModels.find((m) => m.modelId === modelId)
      if (!match) return
      setPanels((prev) =>
        prev.map((p, i) =>
          i === panelIndex ? { ...p, model: match.modelId, provider: match.provider } : p
        )
      )
    },
    [allModels]
  )

  // Listen for status updates from iframes
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const data = event.data
      if (data?.type !== 'arena_status') return
      setPanels((prev) =>
        prev.map((p) => (p.id === data.panelId ? { ...p, status: data.status } : p))
      )
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])

  const broadcastMessage = useCallback(() => {
    const content = input.trim()
    if (!content) return

    setHasSubmitted(true)
    setInput('')

    // Broadcast to each iframe
    panels.forEach((panel, i) => {
      const iframe = iframeRefs.current[i]
      if (iframe?.contentWindow) {
        iframe.contentWindow.postMessage(
          {
            type: 'arena_message',
            content,
            model: panel.model,
            provider: panel.provider,
          },
          '*'
        )
      }
    })

    inputRef.current?.focus()
  }, [input, panels])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        broadcastMessage()
      }
    },
    [broadcastMessage]
  )

  const anyStreaming = panels.some((p) => p.status === 'streaming')

  return (
    <div className="flex flex-col h-screen bg-[#1a1a2e] text-gray-100">
      {/* Header */}
      <header className="shrink-0 flex items-center gap-3 px-4 py-2 border-b border-white/10 bg-[#12122a]">
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-white/60 hover:text-white"
          onClick={() => { window.location.hash = '' }}
        >
          <ArrowLeft size={14} />
          <span className="text-xs">Home</span>
        </Button>

        <h1 className="text-sm font-bold text-cyan-300 tracking-wide">Arena</h1>

        <div className="ml-auto flex items-center gap-2">
          {/* Panel count toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-white/60 hover:text-white"
            onClick={togglePanelCount}
            title={`Switch to ${panelCount === 3 ? '2' : '3'} panels`}
          >
            {panelCount === 3 ? <Columns2 size={14} /> : <Columns3 size={14} />}
            <span className="text-xs">{panelCount === 3 ? '2 Panels' : '3 Panels'}</span>
          </Button>
        </div>
      </header>

      {/* Model pickers row */}
      <div className="shrink-0 flex border-b border-white/10 bg-[#12122a]/50">
        {panels.map((panel, i) => (
          <div
            key={panel.id}
            className="flex-1 flex items-center gap-2 px-3 py-1.5"
            style={{ borderRight: i < panels.length - 1 ? '1px solid rgba(255,255,255,0.1)' : undefined }}
          >
            <select
              value={panel.model}
              onChange={(e) => updatePanelModel(i, e.target.value)}
              disabled={hasSubmitted}
              className="flex-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-gray-200 font-mono focus:outline-none focus:border-cyan-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {providersLoading && <option>Loading...</option>}
              {allModels.map((m) => (
                <option key={`${m.provider}-${m.modelId}`} value={m.modelId}>
                  {m.providerName}: {m.modelName}
                </option>
              ))}
            </select>
            <div
              className="w-2 h-2 rounded-full shrink-0"
              title={panel.status}
              style={{
                backgroundColor:
                  panel.status === 'streaming'
                    ? '#facc15'
                    : panel.status === 'done' || panel.status === 'connected'
                      ? '#22d3ee'
                      : panel.status === 'error'
                        ? '#ef4444'
                        : '#555',
              }}
            />
          </div>
        ))}
      </div>

      {/* Iframes */}
      <div className="flex-1 flex min-h-0">
        {panels.map((panel, i) => (
          <div
            key={panel.id}
            className="flex-1 min-w-0"
            style={{ borderRight: i < panels.length - 1 ? '1px solid rgba(255,255,255,0.1)' : undefined }}
          >
            <iframe
              ref={(el) => { iframeRefs.current[i] = el }}
              src={`#/arena/chat?panel=${panel.id}`}
              className="w-full h-full border-0"
              title={`Arena panel ${i + 1}: ${panel.model}`}
            />
          </div>
        ))}
      </div>

      {/* Bottom input bar */}
      <div className="shrink-0 flex items-center gap-2 px-4 py-3 border-t border-white/10 bg-[#12122a]">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={anyStreaming ? 'Waiting for responses...' : 'Ask all models a question...'}
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder:text-white/30 focus:outline-none focus:border-cyan-500/50"
        />
        <Button
          onClick={broadcastMessage}
          disabled={!input.trim() || anyStreaming}
          className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2.5 rounded-lg disabled:opacity-40"
        >
          <Send size={16} />
        </Button>
      </div>
    </div>
  )
}
