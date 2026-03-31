/**
 * Workspace Chat
 *
 * Main chat area for the IdeaForge Workspace feature. Manages message
 * display, user input, and WebSocket communication for a single
 * conversation. Merges initial REST-loaded messages with live WebSocket
 * messages using Map-based deduplication. Handles both new conversation
 * creation (conversationId === null) and resuming existing conversations.
 *
 * Phase 4 additions: fork/inject/export actions via header dropdown,
 * injection indicator, draft persistence, smart auto-scroll.
 */

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import {
  Send,
  Loader2,
  MessageSquare,
  MoreHorizontal,
  GitFork,
  ArrowDownToLine,
  Download,
  X,
  WifiOff,
  Paperclip,
  ImagePlus,
  Radio,
  Check,
  ChevronDown,
  ScrollText,
  BookOpen,
  Square,
  Eye,
  EyeOff,
  LogOut,
} from 'lucide-react'
import { useWorkspaceChat } from '@/hooks/useWorkspaceChat'
import { useWorkspaceConversation, useWorkspaceProviders } from '@/hooks/useWorkspaceConversations'
import { ChatMessage } from '@/components/ChatMessage'
import { isSubmitEnter } from '@/lib/keyboard'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getWorkspaceSummary, regenerateWorkspaceSummary, exportConversationMarkdown, updateWorkspaceConversation, getSettings, updateSettings } from '@/lib/api'
import { Switch } from '@/components/ui/switch'
import { CountdownTimerBar } from './CountdownTimerBar'
import { WorkspaceChatHeader } from './WorkspaceChatHeader'
import { getContextWarningClass, formatTokenCount } from './EnhancedContextBudgetBar'
import { UsageDashboard } from './UsageDashboard'
import { AutoSummaryPin } from './AutoSummaryPin'
import { ChatForkModal } from './ChatForkModal'
import { InjectFromChatModal } from './InjectFromChatModal'
import { TokenLogPanel } from './TokenLogPanel'
import { AgentNotifications, stripStructuredBlocks, parseStructuredBlocks } from './AgentNotifications'
import { SaveToLibraryModal } from './SaveToLibraryModal'
import { LibraryPickerModal } from './LibraryPickerModal'
import { parseUtcTimestamp } from '@/lib/utils'
import type { ChatMessage as ChatMessageType, WorkspaceMessage, PendingInjection, ImageAttachment, WalkieTalkieLogEntry, LibraryFile } from '@/lib/types'

const DRAFT_KEY_PREFIX = 'workspace-draft-'
const TOKEN_LOG_MODE_KEY = 'workspace-token-log-mode'

/** Tiny elapsed-time counter so the user can tell the agent is still alive. */
function ElapsedTimer({ active }: { active: boolean }) {
  const [seconds, setSeconds] = useState(0)
  const startRef = useRef(Date.now())
  useEffect(() => {
    if (!active) { setSeconds(0); startRef.current = Date.now(); return }
    startRef.current = Date.now()
    const id = setInterval(() => setSeconds(Math.floor((Date.now() - startRef.current) / 1000)), 1000)
    return () => clearInterval(id)
  }, [active])
  if (!active || seconds < 2) return null
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return <span className="text-[10px] tabular-nums text-muted-foreground/60">{m > 0 ? `${m}m ${s}s` : `${s}s`}</span>
}

/** Three-state toggle for the token log side panel. */
type TokenLogMode = 'auto' | 'on' | 'off'

/** Load saved token log mode from localStorage, defaulting to 'auto'. */
function loadTokenLogMode(): TokenLogMode {
  const saved = localStorage.getItem(TOKEN_LOG_MODE_KEY)
  if (saved === 'auto' || saved === 'on' || saved === 'off') return saved
  return 'auto'
}

interface WorkspaceChatProps {
  conversationId: number | null
  onConversationCreated: (id: number) => void
  onNewConversation?: () => void
  chatInputRef?: React.RefObject<HTMLTextAreaElement | null>
  /** Optional working directory (e.g. from the RepoSelector) for the agent session. */
  workingDirectory?: string | null
  /**
   * Lock the context mode for this panel. When set, the mode toggle button is
   * hidden and the panel always uses this mode. Used by split-view to create
   * a "Research (Free/200K)" panel and an "Execute (API/1M)" panel.
   */
  fixedContextMode?: '1m' | '200k'
  /** Optional label shown at the top of the panel (e.g. "Research (Free)"). */
  panelLabel?: string
  /** Callback to send assistant message content to the passoff editor. Shown only in split-view. */
  onCopyToPassoff?: (content: string) => void
  /** Inject a message into this panel's input and auto-send it. Used by the passoff "Send to Execute" button. */
  injectMessage?: string | null
  /** Called after the injected message is consumed, to clear it. */
  onInjectConsumed?: () => void
  /** Called when the agent finishes responding, with the last assistant message content. Used for auto-forward. */
  onResponseComplete?: (content: string) => void
  /** Model to use for this panel ('opus' | 'sonnet'). Passed through to the backend. */
  preferredModel?: 'opus' | 'sonnet'
  /** Callback when the user changes the model for this panel. Only used in split-view. */
  onModelChange?: (model: 'opus' | 'sonnet') => void
  /** Callback with the walkie-talkie log, called on every update. */
  onWalkieTalkieLog?: (log: WalkieTalkieLogEntry[]) => void
  /**
   * Model chosen at new-chat creation time (from sidebar dropdown).
   * Only used when conversationId is null to determine model for the new session.
   */
  pendingModel?: string
  /**
   * Context mode chosen at new-chat creation time (from sidebar dropdown).
   * Only used when conversationId is null to determine context mode for the new session.
   */
  pendingContextMode?: '1m' | '200k'
  /**
   * Counter that increments on every "New Chat" click from the sidebar dropdown.
   * Forces re-render and input focus even when the same model is selected twice.
   */
  newChatKey?: number
  /**
   * Effort level chosen at new-chat creation time (from sidebar dropdown).
   * Only used when conversationId is null. For existing conversations,
   * effort is read from the conversation data.
   */
  pendingEffort?: 'low' | 'medium' | 'high'
  /** Called when agent streaming starts or stops, so the sidebar can show an activity indicator. */
  onStreamingChange?: (isStreaming: boolean) => void
  /** CLI provider for this pane ('claude' | 'codex' | 'gemini'). Passed to backend on conversation create. */
  provider?: 'claude' | 'codex' | 'gemini'
}

/** Generate a unique ID for local messages. */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Build a dedup key for a message to detect duplicates across REST and
 * WebSocket sources.
 */
function dedupKey(msg: ChatMessageType): string {
  return `${msg.role}:${msg.timestamp.getTime()}:${msg.content.slice(0, 80)}`
}

/** Convert a File to an ImageAttachment (base64). */
async function fileToImageAttachment(file: File): Promise<ImageAttachment> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      const base64Data = result.split(',')[1] // Remove data:...;base64, prefix
      resolve({
        id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
        filename: file.name,
        mimeType: file.type as 'image/jpeg' | 'image/png',
        base64Data,
        previewUrl: result,
        size: file.size,
      })
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

/** Convert a File to a text string for inline inclusion. */
async function fileToText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

/** Main chat area with messages, input, and WebSocket communication. */
export function WorkspaceChat({
  conversationId,
  onConversationCreated,
  onNewConversation,
  chatInputRef: externalInputRef,
  workingDirectory,
  fixedContextMode,
  panelLabel,
  onCopyToPassoff,
  injectMessage,
  onInjectConsumed,
  onResponseComplete,
  preferredModel,
  onModelChange,
  onWalkieTalkieLog,
  pendingModel,
  pendingContextMode: pendingContextModeProp,
  newChatKey,
  pendingEffort: pendingEffortProp,
  onStreamingChange,
  provider: providerProp,
}: WorkspaceChatProps): React.JSX.Element {
  const [inputValue, setInputValue] = useState('')
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const internalInputRef = useRef<HTMLTextAreaElement>(null)
  const inputRef = externalInputRef ?? internalInputRef
  const lastConversationIdRef = useRef<number | null | undefined>(undefined)
  const lastSessionModelRef = useRef<string | null>(null)
  const lastSessionContextRef = useRef<string | null>(null)
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false)
  const [showForkModal, setShowForkModal] = useState(false)
  const [showInjectModal, setShowInjectModal] = useState(false)
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  const [pendingImages, setPendingImages] = useState<ImageAttachment[]>([])
  const [attachedLibraryFiles, setAttachedLibraryFiles] = useState<LibraryFile[]>([])
  const [showLibraryPicker, setShowLibraryPicker] = useState(false)
  const [saveToLibraryContent, setSaveToLibraryContent] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  // Token log side panel: 3-state toggle (auto / on / off)
  const [tokenLogMode, setTokenLogMode] = useState<TokenLogMode>(loadTokenLogMode)
  // Whether the panel is currently visible (driven by mode + auto logic)
  const [tokenLogAutoVisible, setTokenLogAutoVisible] = useState(false)

  // Walkie-talkie state
  const [firstMessageSent, setFirstMessageSent] = useState(false)
  const [walkieTalkieInput, setWalkieTalkieInput] = useState('')
  const [walkieTalkieSent, setWalkieTalkieSent] = useState(false)
  const walkieTalkieSentTimerRef = useRef<number | null>(null)
  const walkieTalkieInputRef = useRef<HTMLInputElement>(null)
  // Walkie-talkie settings (loaded from server)
  const [commCheckFrequency, setCommCheckFrequency] = useState<string>('per_feature')
  const [commWaitTimeout, setCommWaitTimeout] = useState(120)
  const [commAutoReply, setCommAutoReply] = useState(true)
  const [showWalkieTalkieSettings, setShowWalkieTalkieSettings] = useState(false)
  const [isSavingSettings, setIsSavingSettings] = useState(false)

  // Browser visibility toggle (headless vs visible) — default visible so user can peek anytime
  const [playwrightHeadless, setPlaywrightHeadless] = useState(false)

  // Context mode: "1m" (1,000,000 tokens with beta) or "200k" (200,000 tokens standard).
  // When fixedContextMode is set (split-view), the mode is locked and the toggle is hidden.
  // For normal (non-split) mode, the context mode is now determined at chat creation time
  // via the New Chat dropdown, and stored per-conversation on the backend.
  //
  // sessionContextMode = what the CURRENT session is actually running on (drives gauge display).
  // It is derived from the conversation's stored context_mode (or the pending prop for new chats).
  const [sessionContextMode, setSessionContextMode] = useState<'1m' | '200k'>(
    fixedContextMode ?? pendingContextModeProp ?? '200k'
  )

  // Cache the last known context_mode from the database so it persists across
  // React Query refetch gaps (where conversationDetail is temporarily undefined).
  // This prevents the badge from flickering to '200k' during invalidation cycles.
  const [knownContextMode, setKnownContextMode] = useState<'1m' | '200k' | null>(null)
  const knownConversationIdRef = useRef<number | null>(null)

  // NOTE: knownContextMode reset and conversationDetail persistence effects
  // are defined below, after useWorkspaceChat and useWorkspaceConversation hooks.

  // Provider-aware model presets (used for read-only display in the header badge).
  const { data: wsProviders } = useWorkspaceProviders()
  const effectiveProvider = providerProp ?? 'claude'
  type ModelPreset = { model: string; context: '1m' | '200k'; label: string }
  const MODEL_PRESETS: ModelPreset[] = useMemo(() => {
    const CLAUDE_FALLBACK: ModelPreset[] = [
      { model: 'opus', context: '200k', label: 'Opus 4.6 · 200K' },
      { model: 'sonnet', context: '200k', label: 'Sonnet 4.6 · 200K' },
      { model: 'haiku', context: '200k', label: 'Haiku · 200K' },
      { model: 'opus', context: '1m', label: 'Opus 4.6 · 1M' },
      { model: 'sonnet', context: '1m', label: 'Sonnet 4.6 · 1M' },
    ]
    if (!wsProviders || !wsProviders[effectiveProvider]) return CLAUDE_FALLBACK
    const pDef = wsProviders[effectiveProvider]
    if (effectiveProvider === 'claude') {
      return [
        ...pDef.models.map((m: { id: string; name: string }) => ({ model: m.id, context: '200k' as const, label: `${m.name} · 200K` })),
        ...pDef.models.filter((m: { id: string; name: string }) => m.id !== 'haiku').map((m: { id: string; name: string }) => ({ model: m.id, context: '1m' as const, label: `${m.name} · 1M` })),
      ]
    }
    // Non-Claude: base + optional 1M
    return pDef.models.flatMap((m: { id: string; name: string; supports_1m?: boolean }) => {
      const base: ModelPreset[] = [{ model: m.id, context: '200k' as const, label: m.name }]
      if (m.supports_1m) {
        base.push({ model: m.id, context: '1m' as const, label: `${m.name} · 1M` })
      }
      return base
    })
  }, [wsProviders, effectiveProvider])

  // Keep sessionContextMode in sync when fixedContextMode changes (split-view)
  useEffect(() => {
    if (fixedContextMode) {
      setSessionContextMode(fixedContextMode)
    }
  }, [fixedContextMode])

  // Load walkie-talkie settings from the server on mount
  useEffect(() => {
    getSettings()
      .then((s) => {
        if (s.comm_check_frequency) setCommCheckFrequency(s.comm_check_frequency)
        if (s.comm_wait_timeout) setCommWaitTimeout(s.comm_wait_timeout)
        if (s.comm_auto_reply !== undefined) setCommAutoReply(s.comm_auto_reply)
        if (s.playwright_headless !== undefined) setPlaywrightHeadless(s.playwright_headless)
      })
      .catch(() => { /* use defaults */ })
  }, [])

  // Clean up sent confirmation timer on unmount
  useEffect(() => {
    return () => {
      if (walkieTalkieSentTimerRef.current) {
        clearTimeout(walkieTalkieSentTimerRef.current)
      }
    }
  }, [])

  // Memoize error handler to keep hook reference stable
  const handleError = useCallback((error: string) => {
    console.error('Workspace chat error:', error)
  }, [])

  // WebSocket-based chat hook
  const {
    messages: liveMessages,
    isLoading,
    connectionStatus,
    lastError,
    conversationId: activeConversationId,
    totalTokens,
    contextBudget,
    pendingInjection,
    setPendingInjection,
    agentWaiting,
    agentWaitingQuestion,
    walkieTalkieLog,
    addWalkieTalkieEntry,
    tokenLog,
    clearTokenLog,
    modelId,
    cancelSession,
    start,
    sendMessage,
    sendWalkieTalkie,
    disconnect,
    clearMessages,
  } = useWorkspaceChat({ onError: handleError })

  // Notify parent when streaming state changes (for sidebar activity indicator).
  // Intentionally omit onStreamingChange from deps to avoid re-render loops
  // when the parent passes an unstable callback reference (inline arrow).
  useEffect(() => {
    onStreamingChange?.(isLoading)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading])

  // Compute API token totals from the token log entries.
  // For input/output/cost: sum across all turns (billing-relevant totals).
  // For cache: use the LATEST result_summary only (current context state).
  // Each turn's cache_read includes all previously cached content, so summing
  // them would massively over-count (e.g. 100K + 200K + 300K = 600K when
  // the actual cache is 300K).
  //
  // IMPORTANT: The SDK's ResultMessage.usage is CUMULATIVE across all API
  // turns in the session (including sub-agent turns). So api_input_tokens
  // from a result_summary is NOT the current context window fill — it's
  // the total input across all API calls. For the context bar, we use
  // cache_read + cache_create as the best proxy for current context window
  // utilization (these represent the actual cached context state), capped
  // at the context window size.
  const apiTokenTotals = useMemo(() => {
    let apiInput = 0
    let apiOutput = 0
    let totalCost = 0
    let latestCacheRead = 0
    let latestCacheCreate = 0
    let latestInput = 0
    for (const e of tokenLog) {
      if (e.event_type === 'result_summary') {
        apiInput += e.api_input_tokens ?? 0
        apiOutput += e.api_output_tokens ?? 0
        totalCost += e.api_total_cost_usd ?? 0
        // Track the latest turn's values for current context state
        latestCacheRead = e.api_cache_read_tokens ?? 0
        latestCacheCreate = e.api_cache_creation_tokens ?? 0
        latestInput = e.api_input_tokens ?? 0
      }
    }
    // currentContext = best estimate of actual context window fill level.
    // Use cache_read + cache_create as proxy (reflects real cached state).
    // Cap at context window — the SDK's cumulative input_tokens can exceed
    // the window when sub-agents or multiple tool-use turns are involved.
    const ctxWindow = sessionContextMode === '1m' ? 1_000_000 : 200_000
    const rawContext = latestCacheRead + latestCacheCreate + latestInput
    const currentContext = Math.min(rawContext, ctxWindow)
    return { apiInput, apiOutput, cacheRead: latestCacheRead, totalCost, currentContext }
  }, [tokenLog, sessionContextMode])

  // ── Context window threshold warnings ──────────────────────────────
  // Inject system messages into the chat when context usage crosses
  // key thresholds so both the user AND the agent can see them.
  const firedThresholdsRef = useRef<Set<number>>(new Set())
  const contextBudgetTotal = sessionContextMode === '1m' ? 1_000_000 : 200_000

  const [contextWarnings, setContextWarnings] = useState<Array<{
    id: string; role: 'system'; content: string; timestamp: Date
  }>>([])

  useEffect(() => {
    if (apiTokenTotals.currentContext <= 0) return
    const pct = (apiTokenTotals.currentContext / contextBudgetTotal) * 100
    const fired = firedThresholdsRef.current

    const thresholds: Array<{ at: number; msg: string }> = [
      { at: 50, msg: '[CONTEXT 50%] Start wrapping up. Begin handoff preparation.' },
      { at: 51, msg: '[CONTEXT 51%] HARD STOP — coding must stop now. Commit work and hand off to next session.' },
      { at: 55, msg: '[CONTEXT 55%] Quality degrading. PRDs and discussion only — no code generation.' },
      { at: 60, msg: '[CONTEXT 60%] Session should wrap up soon. Auto-generating handoff summary recommended.' },
    ]

    for (const t of thresholds) {
      if (pct >= t.at && !fired.has(t.at)) {
        fired.add(t.at)
        setContextWarnings(prev => [...prev, {
          id: `ctx-warn-${t.at}-${Date.now()}`,
          role: 'system' as const,
          content: t.msg,
          timestamp: new Date(),
        }])
      }
    }
  }, [apiTokenTotals.currentContext, contextBudgetTotal])

  // Propagate walkie-talkie log to parent for display in sidebar panel
  useEffect(() => {
    onWalkieTalkieLog?.(walkieTalkieLog)
  }, [walkieTalkieLog, onWalkieTalkieLog])

  // Focus walkie-talkie input when agent enters waiting state
  useEffect(() => {
    if (agentWaiting) {
      walkieTalkieInputRef.current?.focus()
    }
  }, [agentWaiting])

  // REST query for initial messages when resuming a conversation
  const { data: conversationDetail, isLoading: isLoadingConversation } =
    useWorkspaceConversation(conversationId)

  // Effort level — read from conversation data (set at chat creation time).
  // For new chats, uses pendingEffortProp from the sidebar.
  // This is read-only in the chat area; effort is only chosen at chat start.
  const conversationEffort: 'low' | 'medium' | 'high' =
    conversationDetail?.effort
    ?? pendingEffortProp
    ?? 'high'
  // Alias for backward-compat in cost_settings payloads
  const effortLevel = conversationEffort

  // Derive the active model from the conversation data (read-only display).
  // For split-view panels, use preferredModel. For normal mode, use the conversation's model field.
  // Model can be any string (e.g. 'opus', 'sonnet', 'o3', 'pro', 'flash', etc.)
  const conversationModel: string = preferredModel
    ?? conversationDetail?.model
    ?? pendingModel
    ?? (effectiveProvider === 'claude' ? 'opus' : wsProviders?.[effectiveProvider]?.default_model ?? 'opus')
  const conversationContextMode: '1m' | '200k' = fixedContextMode
    ?? conversationDetail?.context_mode
    ?? knownContextMode
    ?? pendingContextModeProp
    ?? '200k'

  // Derive the active preset index from the conversation's actual model + context_mode (read-only).
  const activePresetIndex = useMemo(() => {
    return MODEL_PRESETS.findIndex(
      p => p.model === conversationModel && p.context === conversationContextMode
    )
  }, [conversationModel, conversationContextMode, MODEL_PRESETS])

  // Sync sessionContextMode from conversation data when switching conversations
  useEffect(() => {
    if (!fixedContextMode && conversationDetail) {
      if (conversationDetail.context_mode) {
        setSessionContextMode(conversationDetail.context_mode)
      }
    }
  }, [conversationDetail, fixedContextMode])

  // Reset knownContextMode when switching to a different conversation
  // (moved here so activeConversationId and conversationDetail are in scope)
  useEffect(() => {
    const effId = conversationId ?? activeConversationId
    if (effId !== knownConversationIdRef.current) {
      knownConversationIdRef.current = effId
      setKnownContextMode(null)
    }
  }, [conversationId, activeConversationId])

  // Persist the DB value whenever conversationDetail loads
  useEffect(() => {
    if (conversationDetail?.context_mode) {
      setKnownContextMode(conversationDetail.context_mode as '1m' | '200k')
    }
  }, [conversationDetail?.context_mode])

  // Summary query and mutation for auto-summary pin
  const queryClient = useQueryClient()

  const { data: summary } = useQuery({
    queryKey: ['workspace', 'summary', conversationId ?? activeConversationId],
    queryFn: () => getWorkspaceSummary((conversationId ?? activeConversationId)!),
    enabled: (conversationId ?? activeConversationId) !== null,
  })

  const regenerateMutation = useMutation({
    mutationFn: () => regenerateWorkspaceSummary((conversationId ?? activeConversationId)!),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['workspace', 'summary', conversationId ?? activeConversationId],
      })
    },
  })

  // Context budget usage for warning state (follows the ACTIVE session mode, not pending)
  const displayBudget = sessionContextMode === '1m' ? 1_000_000 : 200_000
  const usagePercent = contextBudget.messageTokens > 0 && displayBudget > 0
    ? ((contextBudget.messageTokens + contextBudget.summaryTokens) / displayBudget) * 100
    : 0

  // Notify parent when a new conversation is created via WebSocket
  const previousActiveIdRef = useRef<number | null>(activeConversationId)
  useEffect(() => {
    const hadNone = previousActiveIdRef.current === null
    const hasNow = activeConversationId !== null

    if (hadNone && hasNow) {
      onConversationCreated(activeConversationId)
    }

    previousActiveIdRef.current = activeConversationId
  }, [activeConversationId, onConversationCreated])

  // Start or resume session when conversationId changes
  useEffect(() => {
    if (isLoadingConversation) return

    // Only act when the ID has actually changed
    if (lastConversationIdRef.current === conversationId) return
    const previousId = lastConversationIdRef.current
    lastConversationIdRef.current = conversationId

    // When a new conversation is created via the active WebSocket (null → new ID),
    // the session already owns this conversation. Don't tear it down.
    if (previousId === null && conversationId !== null && activeConversationId === conversationId) {
      return
    }

    // Genuine switch between conversations — disconnect the old session
    if (previousId !== undefined) {
      disconnect()
      clearMessages()
      setFirstMessageSent(false)
    }

    // Start/resume the selected conversation, passing the working directory
    // so the agent session uses the repo clone as its cwd.
    // Use the conversation's stored context_mode and model (or pending props for new chats).
    if (conversationId !== null) {
      const modeForSession = conversationContextMode
      setSessionContextMode(modeForSession)
      const modelForSession = conversationModel
      lastSessionModelRef.current = modelForSession
      lastSessionContextRef.current = modeForSession
      console.info('[WorkspaceChat] session-switch effect: starting session', {
        conversationId, modeForSession, modelForSession, previousId,
      })
      start(conversationId, workingDirectory ?? undefined, modeForSession, { effort: effortLevel }, modelForSession, providerProp)
    }
  }, [conversationId, isLoadingConversation, activeConversationId, start, disconnect, clearMessages, workingDirectory, conversationModel, conversationContextMode, effortLevel, providerProp])

  // Reconnect when badge cycling or split-view toggle changes the conversation's
  // model or context mode while a session is already active. We intentionally do
  // NOT guard on isLoading: when the user explicitly switches models, the running
  // session must be torn down and restarted even if a response is in flight.
  useEffect(() => {
    if (!conversationId || !lastSessionModelRef.current) return
    if (isLoadingConversation) return
    const modelChanged = conversationModel !== lastSessionModelRef.current
    const contextChanged = lastSessionContextRef.current !== null && conversationContextMode !== lastSessionContextRef.current
    if (!modelChanged && !contextChanged) return

    console.info('[WorkspaceChat] badge-cycle reconnect', {
      conversationId, conversationModel, conversationContextMode,
      prevModel: lastSessionModelRef.current, prevContext: lastSessionContextRef.current,
    })

    lastSessionModelRef.current = conversationModel
    lastSessionContextRef.current = conversationContextMode
    setSessionContextMode(conversationContextMode)
    disconnect()
    clearMessages()
    setFirstMessageSent(false)
    start(conversationId, workingDirectory ?? undefined, conversationContextMode, { effort: effortLevel }, conversationModel, providerProp)
  }, [conversationModel, conversationContextMode, conversationId, isLoadingConversation, disconnect, clearMessages, start, workingDirectory, effortLevel, providerProp])

  // Smart auto-scroll: only scroll if user is near the bottom
  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current
    if (!container) return
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight
    setIsUserScrolledUp(distanceFromBottom > 100)
  }, [])

  useEffect(() => {
    if (!isUserScrolledUp) {
      messagesContainerRef.current?.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth',
      })
    }
  }, [liveMessages.length, isUserScrolledUp])

  // Detect response completion (isLoading true→false) for auto-forward.
  // Intentionally omit onResponseComplete from deps to avoid re-render loops
  // when the parent passes an unstable callback reference.
  const prevLoadingRef = useRef(false)
  const onResponseCompleteRef = useRef(onResponseComplete)
  onResponseCompleteRef.current = onResponseComplete
  useEffect(() => {
    if (prevLoadingRef.current && !isLoading && onResponseCompleteRef.current) {
      const lastMessage = liveMessages[liveMessages.length - 1]
      if (lastMessage?.role === 'assistant' && lastMessage.content) {
        onResponseCompleteRef.current(lastMessage.content)
      }
    }
    prevLoadingRef.current = isLoading
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading, liveMessages])

  // Token log auto-mode: show panel when streaming starts
  useEffect(() => {
    if (tokenLogMode !== 'auto') return
    if (isLoading) {
      setTokenLogAutoVisible(true)
    }
  }, [isLoading, tokenLogMode])

  // Persist token log mode to localStorage
  const handleTokenLogModeChange = useCallback((mode: TokenLogMode) => {
    setTokenLogMode(mode)
    localStorage.setItem(TOKEN_LOG_MODE_KEY, mode)
    // When switching to 'off', immediately hide; 'on' immediately shows
    if (mode === 'off') {
      setTokenLogAutoVisible(false)
    }
  }, [])

  // Compute whether the token log panel should be visible
  const tokenLogVisible = tokenLogMode === 'on' || (tokenLogMode === 'auto' && tokenLogAutoVisible)

  // Handler to dismiss the panel (used by X button and auto mode)
  const handleTokenLogClose = useCallback(() => {
    if (tokenLogMode === 'auto') {
      setTokenLogAutoVisible(false)
    } else if (tokenLogMode === 'on') {
      // When "On" mode, X button switches to Off
      handleTokenLogModeChange('off')
    }
  }, [tokenLogMode, handleTokenLogModeChange])

  // Focus input when not loading
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus()
    }
  }, [isLoading, inputRef])

  // Focus input when user clicks a model from the New Chat dropdown
  useEffect(() => {
    if (newChatKey && newChatKey > 0) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [newChatKey, inputRef])

  // Draft persistence: load draft when switching conversations
  useEffect(() => {
    if (conversationId !== null) {
      const draft = localStorage.getItem(`${DRAFT_KEY_PREFIX}${conversationId}`)
      setInputValue(draft || '')
    } else {
      setInputValue('')
    }
  }, [conversationId])

  // Draft persistence: save draft on input change (debounced)
  useEffect(() => {
    const effectiveId = conversationId ?? activeConversationId
    if (!effectiveId) return
    const timer = setTimeout(() => {
      if (inputValue) {
        localStorage.setItem(`${DRAFT_KEY_PREFIX}${effectiveId}`, inputValue)
      } else {
        localStorage.removeItem(`${DRAFT_KEY_PREFIX}${effectiveId}`)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [inputValue, conversationId, activeConversationId])

  // Handle injected messages (e.g. from passoff "Send to Execute")
  useEffect(() => {
    if (!injectMessage || isLoading) return
    // If no conversation yet, start a new one
    if (conversationId === null && activeConversationId === null) {
      start(undefined, workingDirectory ?? undefined, conversationContextMode, { effort: effortLevel }, conversationModel, providerProp)
    }
    sendMessage(injectMessage)
    onInjectConsumed?.()
  }, [injectMessage]) // eslint-disable-line react-hooks/exhaustive-deps

  // Convert REST messages to ChatMessageType format for merging
  const initialMessages: ChatMessageType[] = useMemo(() => {
    if (!conversationDetail?.messages) return []
    return conversationDetail.messages.map((m) => ({
      id: `rest-${m.id}`,
      role: m.role,
      content: m.content,
      timestamp: m.timestamp ? parseUtcTimestamp(m.timestamp) : new Date(),
    }))
  }, [conversationDetail])

  // Merge initial (REST) messages with live (WebSocket) messages, deduplicating
  const displayMessages: ChatMessageType[] = useMemo(() => {
    let merged: ChatMessageType[]
    if (initialMessages.length === 0) merged = liveMessages
    else if (liveMessages.length === 0) merged = initialMessages
    else {
      const seen = new Map<string, ChatMessageType>()
      for (const msg of initialMessages) {
        seen.set(dedupKey(msg), msg)
      }
      for (const msg of liveMessages) {
        // Live messages take precedence (may have streaming state)
        seen.set(dedupKey(msg), msg)
      }
      merged = Array.from(seen.values())
    }
    // Append context warnings as system messages at the end
    if (contextWarnings.length > 0) {
      return [...merged, ...contextWarnings]
    }
    return merged
  }, [initialMessages, liveMessages, contextWarnings])

  // Build WorkspaceMessage[] for the fork modal from REST conversation detail
  const forkableMessages: WorkspaceMessage[] = useMemo(() => {
    if (!conversationDetail?.messages) return []
    return conversationDetail.messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({
        id: m.id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        token_estimate: m.token_estimate,
        timestamp: m.timestamp,
      }))
  }, [conversationDetail])

  // Image processing: convert image files to base64 ImageAttachment objects
  const processImageFiles = useCallback(async (files: File[]) => {
    const imageFiles = files.filter(f =>
      f.type === 'image/jpeg' || f.type === 'image/png' || f.type === 'image/gif' || f.type === 'image/webp'
    )
    if (imageFiles.length === 0) return

    const maxSize = 10 * 1024 * 1024 // 10MB
    const validFiles = imageFiles.filter(f => f.size <= maxSize)

    const newAttachments = await Promise.all(validFiles.map(fileToImageAttachment))
    setPendingImages(prev => [...prev, ...newAttachments])
  }, [])

  // File processing: separate images from other files
  const processFiles = useCallback(async (files: File[]) => {
    const imageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    const images = files.filter(f => imageTypes.includes(f.type))
    const otherFiles = files.filter(f => !imageTypes.includes(f.type))

    if (images.length > 0) {
      await processImageFiles(images)
    }

    if (otherFiles.length > 0) {
      setPendingFiles(prev => [...prev, ...otherFiles])
    }
  }, [processImageFiles])

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    // Only set dragging false if we're leaving the drop zone entirely
    if (e.currentTarget === e.target) {
      setIsDragging(false)
    }
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      await processFiles(files)
    }
  }, [processFiles])

  // Clipboard paste handler for images
  const handlePaste = useCallback(async (e: React.ClipboardEvent) => {
    const items = Array.from(e.clipboardData.items)
    const imageItems = items.filter(item => item.type.startsWith('image/'))

    if (imageItems.length > 0) {
      e.preventDefault() // Prevent default paste behavior for images
      const files = imageItems
        .map(item => item.getAsFile())
        .filter((f): f is File => f !== null)

      await processImageFiles(files)
    }
    // For non-image paste, let the default textarea behavior handle it
  }, [processImageFiles])

  // Walkie-talkie send handler
  const handleWalkieTalkieSend = useCallback(() => {
    const content = walkieTalkieInput.trim()
    if (!content) return
    addWalkieTalkieEntry('user', content)
    sendWalkieTalkie(content)
    setWalkieTalkieInput('')
    // Show brief "Sent!" confirmation
    setWalkieTalkieSent(true)
    if (walkieTalkieSentTimerRef.current) clearTimeout(walkieTalkieSentTimerRef.current)
    walkieTalkieSentTimerRef.current = window.setTimeout(() => {
      setWalkieTalkieSent(false)
      walkieTalkieSentTimerRef.current = null
    }, 1500)
  }, [walkieTalkieInput, sendWalkieTalkie, addWalkieTalkieEntry])

  // Walkie-talkie input keydown handler
  const handleWalkieTalkieKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleWalkieTalkieSend()
      }
    },
    [handleWalkieTalkieSend],
  )

  // CountdownTimerBar handlers
  const handleTimerTimeout = useCallback(() => {
    // Auto-reply: send "Continue with your best judgment" to the agent
    addWalkieTalkieEntry('system', 'Auto-reply: Continue with your best judgment')
    sendWalkieTalkie('Continue with your best judgment')
  }, [sendWalkieTalkie, addWalkieTalkieEntry])

  const handleTimerKeepGoing = useCallback(() => {
    // "Keep Going" button: send immediate response
    addWalkieTalkieEntry('user', 'Keep going, proceed with your best judgment')
    sendWalkieTalkie('Keep going, proceed with your best judgment')
  }, [sendWalkieTalkie, addWalkieTalkieEntry])

  // Save a walkie-talkie setting to the server and update local state
  const saveWalkieTalkieSetting = useCallback(async (patch: { comm_check_frequency?: string; comm_wait_timeout?: number; comm_auto_reply?: boolean }) => {
    setIsSavingSettings(true)
    try {
      const updated = await updateSettings(patch)
      if (updated.comm_check_frequency) setCommCheckFrequency(updated.comm_check_frequency)
      if (updated.comm_wait_timeout) setCommWaitTimeout(updated.comm_wait_timeout)
      if (updated.comm_auto_reply !== undefined) setCommAutoReply(updated.comm_auto_reply)
    } catch {
      // Silently fail — settings will use current local state
    } finally {
      setIsSavingSettings(false)
    }
  }, [])

  // Whether walkie-talkie UI should be visible
  const walkieTalkieVisible = isLoading && commCheckFrequency !== 'never'

  // Send handler — routes through walkie-talkie when agent is already in a turn
  const handleSend = useCallback(async () => {
    let content = inputValue.trim()
    if (!content && pendingImages.length === 0 && pendingFiles.length === 0) return

    // If agent is in an active turn and we've already sent the first message,
    // route through walkie-talkie instead of starting a new API turn.
    // This is dramatically cheaper — no full conversation history resend.
    if (isLoading && firstMessageSent) {
      console.info('[WorkspaceChat] handleSend: routing via walkie-talkie (turn active)')
      sendWalkieTalkie(content)
      addWalkieTalkieEntry('user', content)
      setInputValue('')
      const textarea = inputRef.current
      if (textarea) {
        textarea.style.height = 'auto'
      }
      return
    }

    if (isLoading) return

    // Append file contents as text
    if (pendingFiles.length > 0) {
      const fileContents = await Promise.all(
        pendingFiles.map(async (file) => {
          try {
            const text = await fileToText(file)
            return `\n--- File: ${file.name} ---\n${text}\n--- End: ${file.name} ---`
          } catch {
            return `\n--- File: ${file.name} (could not read) ---`
          }
        })
      )
      content = content + fileContents.join('\n')
    }

    const attachments = pendingImages.length > 0 ? [...pendingImages] : undefined
    const libraryIds = attachedLibraryFiles.length > 0 ? attachedLibraryFiles.map(f => f.id) : undefined

    // If no conversation yet, start a new one first. The hook will queue
    // the message and dispatch it once the session is ready.
    // Pass workingDirectory so the new session uses the selected repo.
    if (conversationId === null && activeConversationId === null) {
      console.info('[WorkspaceChat] handleSend: starting new session', {
        conversationContextMode, conversationModel, conversationId, activeConversationId,
      })
      start(undefined, workingDirectory ?? undefined, conversationContextMode, { effort: effortLevel }, conversationModel, providerProp)
    } else {
      console.info('[WorkspaceChat] handleSend: existing session', {
        conversationContextMode, conversationModel, conversationId, activeConversationId,
      })
    }
    sendMessage(content, attachments, libraryIds)
    setFirstMessageSent(true)

    setInputValue('')
    // Reset textarea height back to single row after sending
    const textarea = inputRef.current
    if (textarea) {
      textarea.style.height = 'auto'
    }
    setPendingImages([])
    setPendingFiles([])
    setAttachedLibraryFiles([])
    // Clear draft after sending
    const effectiveId = conversationId ?? activeConversationId
    if (effectiveId) {
      localStorage.removeItem(`${DRAFT_KEY_PREFIX}${effectiveId}`)
    }
  }, [inputValue, isLoading, firstMessageSent, conversationId, activeConversationId, start, sendMessage, sendWalkieTalkie, addWalkieTalkieEntry, workingDirectory, pendingImages, pendingFiles, attachedLibraryFiles, conversationContextMode, conversationModel, effortLevel, providerProp])

  // End Session: gracefully tell the agent to write a handoff and stop
  const handleEndSession = useCallback(() => {
    if (!isLoading) return
    const convId = conversationId ?? activeConversationId ?? 'unknown'
    const endMessage = `End session. Write your handoff summary to .autoforge/handoffs/session-${convId}.md including: summary of what was discussed, decisions made, current state, and next steps. Then stop.`
    sendWalkieTalkie(endMessage)
    addWalkieTalkieEntry('user', 'End Session (handoff requested)')
    setFirstMessageSent(false)
  }, [isLoading, conversationId, activeConversationId, sendWalkieTalkie, addWalkieTalkieEntry])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (isSubmitEnter(e)) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  const effectiveConversationId = conversationId ?? activeConversationId
  const effectiveTitle = conversationDetail?.title ?? null
  const effectiveCategory = conversationDetail?.category ?? 'general'
  const effectiveTags = conversationDetail?.tags ?? ''
  const hasActiveChat = effectiveConversationId !== null

  // Track whether WebSocket reconnection has been exhausted
  const reconnectionExhausted = connectionStatus === 'disconnected' && hasActiveChat

  // Conversation field update handlers: persist changes via the PATCH API
  // and invalidate the query cache so the sidebar stays in sync.
  const handleUpdateTitle = useCallback(
    (newTitle: string) => {
      if (!effectiveConversationId) return
      updateWorkspaceConversation(effectiveConversationId, { title: newTitle })
        .then(() => queryClient.invalidateQueries({ queryKey: ['workspace'] }))
        .catch((err) => console.error('Failed to update title:', err))
    },
    [effectiveConversationId, queryClient],
  )

  const handleUpdateCategory = useCallback(
    (newCategory: string) => {
      if (!effectiveConversationId) return
      updateWorkspaceConversation(effectiveConversationId, { category: newCategory })
        .then(() => queryClient.invalidateQueries({ queryKey: ['workspace'] }))
        .catch((err) => console.error('Failed to update category:', err))
    },
    [effectiveConversationId, queryClient],
  )

  const handleUpdateTags = useCallback(
    (newTags: string) => {
      if (!effectiveConversationId) return
      updateWorkspaceConversation(effectiveConversationId, { tags: newTags })
        .then(() => queryClient.invalidateQueries({ queryKey: ['workspace'] }))
        .catch((err) => console.error('Failed to update tags:', err))
    },
    [effectiveConversationId, queryClient],
  )

  // Empty state when no conversation is selected or created via WebSocket.
  // Check BOTH conversationId (prop from parent) and activeConversationId (from WS hook)
  // to prevent showing empty state when a conversation was just created via WebSocket
  // but the parent hasn't propagated the update yet.
  const showEmptyState = conversationId === null && activeConversationId === null && displayMessages.length === 0

  const handleExport = useCallback(() => {
    if (effectiveConversationId) {
      exportConversationMarkdown(effectiveConversationId)
    }
  }, [effectiveConversationId])

  const handleForkCreated = useCallback((newId: number) => {
    setShowForkModal(false)
    onConversationCreated(newId)
    queryClient.invalidateQueries({ queryKey: ['workspace', 'conversations'] })
  }, [onConversationCreated, queryClient])

  const handleInject = useCallback((injection: PendingInjection) => {
    setPendingInjection(injection)
    setShowInjectModal(false)
  }, [setPendingInjection])

  return (
    <div className="flex h-full">
      {/* Left side panel: Token Log */}
      {tokenLogVisible && (
        <TokenLogPanel
          entries={tokenLog}
          conversationId={conversationId ?? activeConversationId}
          onClose={handleTokenLogClose}
          onClear={clearTokenLog}
        />
      )}

      {/* Main chat content */}
      <div className={`flex flex-col flex-1 min-w-0 h-full bg-background transition-colors duration-500 ${getContextWarningClass(usagePercent)}`}>
      {/* Header with actions dropdown */}
      <div className="flex items-center border-b border-border bg-card">
        <div className="flex-1">
          <WorkspaceChatHeader
            conversationId={effectiveConversationId}
            title={effectiveTitle}
            category={effectiveCategory}
            tags={effectiveTags}
            connectionStatus={connectionStatus}
            onUpdateTitle={handleUpdateTitle}
            onUpdateCategory={handleUpdateCategory}
            onUpdateTags={handleUpdateTags}
            workingDirectory={workingDirectory}
            walkieTalkieActive={walkieTalkieVisible}
            agentWaiting={agentWaiting}
            onToggleSettings={() => setShowWalkieTalkieSettings((v) => !v)}
            settingsOpen={showWalkieTalkieSettings}
            provider={effectiveProvider}
          />
        </div>

        {/* Inline model info: active model badge + model ID + cost */}
        {!fixedContextMode && (
          <div className="flex items-center gap-1.5 px-2 shrink-0">
            {(() => {
              const noActiveChat = conversationId === null && activeConversationId === null
              const hasPendingSelection = noActiveChat && pendingModel != null
              const showPresetIndex = noActiveChat
                ? (hasPendingSelection
                  ? MODEL_PRESETS.findIndex(p => p.model === pendingModel && p.context === (pendingContextModeProp ?? '1m'))
                  : -1)
                : activePresetIndex

              if (noActiveChat && !hasPendingSelection) return null

              const activePreset = MODEL_PRESETS[showPresetIndex]
              if (!activePreset) return null

              // Provider-aware color coding
              const pillClass = effectiveProvider === 'codex'
                ? 'bg-emerald-600 text-white'
                : effectiveProvider === 'gemini'
                  ? 'bg-violet-600 text-white'
                  : activePreset.model === 'sonnet'
                    ? 'bg-violet-500 text-white'
                    : activePreset.context === '1m'
                      ? 'bg-blue-600 text-white'
                      : 'bg-zinc-600 text-white'

              // Provider-aware display ID
              const displayId = modelId
                || (effectiveProvider === 'claude'
                  ? (conversationModel === 'sonnet' ? 'claude-sonnet-4-6' : 'claude-opus-4-6')
                  : conversationModel)

              return (
                <>
                  <span
                    className={`px-2 py-0.5 text-[10px] font-bold rounded-full whitespace-nowrap ${pillClass}`}
                    title={`${activePreset.label} — AutoForge orchestration layer using ${displayId} as the underlying AI model. Context: ${activePreset.context === '1m' ? '1M tokens' : '200K tokens'}.`}
                  >
                    {activePreset.label}
                  </span>
                  <span
                    className="text-[10px] font-mono text-muted-foreground truncate max-w-[140px]"
                    title={modelId ? `Active model: ${modelId}` : `Expected model: ${displayId}`}
                  >
                    {displayId}
                  </span>
                  {apiTokenTotals.totalCost > 0 && (
                    <span
                      className="text-[10px] font-mono text-muted-foreground whitespace-nowrap"
                      title={`Session tokens: ${apiTokenTotals.apiInput.toLocaleString()} input / ${apiTokenTotals.apiOutput.toLocaleString()} output / ${apiTokenTotals.cacheRead.toLocaleString()} cache read`}
                    >
                      ${apiTokenTotals.totalCost.toFixed(3)} · {formatTokenCount(apiTokenTotals.apiInput + apiTokenTotals.apiOutput)} tok
                    </span>
                  )}
                </>
              )
            })()}
          </div>
        )}

        {/* Browser visibility toggle: Headless / Visible */}
        <button
          type="button"
          onClick={async () => {
            const next = !playwrightHeadless
            setPlaywrightHeadless(next)
            try { await updateSettings({ playwright_headless: next }) } catch { setPlaywrightHeadless(!next) }
          }}
          className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold whitespace-nowrap transition-all duration-150 shrink-0 ${
            playwrightHeadless
              ? 'bg-zinc-600 text-white hover:bg-zinc-500'
              : 'bg-amber-500 text-white hover:bg-amber-400'
          }`}
          title={playwrightHeadless ? 'Browser: Headless (invisible) — click to make visible' : 'Browser: Visible (window shown) — click to hide'}
        >
          {playwrightHeadless ? <EyeOff size={10} /> : <Eye size={10} />}
          {playwrightHeadless ? 'Headless' : 'Visible'}
        </button>

        {/* Token log 3-state toggle: Auto | On | Off */}
        <div className="flex items-center gap-1 px-2">
          <ScrollText size={14} className="text-muted-foreground flex-shrink-0" />
          <div className="flex rounded-full border border-border overflow-hidden" role="radiogroup" aria-label="Token log visibility">
            {(['auto', 'on', 'off'] as const).map((mode) => (
              <button
                key={mode}
                role="radio"
                aria-checked={tokenLogMode === mode}
                onClick={() => handleTokenLogModeChange(mode)}
                className={`px-2 py-0.5 text-[10px] font-semibold capitalize transition-all duration-150 ${
                  tokenLogMode === mode
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card text-muted-foreground hover:bg-muted hover:text-foreground'
                } ${mode !== 'off' ? 'border-r border-border' : ''}`}
                title={
                  mode === 'auto' ? 'Show panel automatically when streaming'
                    : mode === 'on' ? 'Always show token log panel'
                      : 'Hide token log panel'
                }
              >
                {mode}
              </button>
            ))}
          </div>
        </div>

        {/* Actions dropdown */}
        {hasActiveChat && (
          <div className="pr-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal size={16} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setShowForkModal(true)}>
                  <GitFork size={14} className="mr-2" />
                  Fork Chat
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setShowInjectModal(true)}>
                  <ArrowDownToLine size={14} className="mr-2" />
                  Inject from Chat
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleExport}>
                  <Download size={14} className="mr-2" />
                  Export as Markdown
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Walkie-Talkie settings panel (collapsible) */}
      {showWalkieTalkieSettings && (
        <div className="border-b border-amber-300 dark:border-amber-700/40 bg-amber-50/50 dark:bg-amber-950/10 px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-amber-700 dark:text-amber-400 uppercase tracking-wide flex items-center gap-1.5">
              <Radio size={12} />
              Walkie-Talkie Settings
            </span>
            <button
              onClick={() => setShowWalkieTalkieSettings(false)}
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Close settings"
            >
              <X size={14} />
            </button>
          </div>

          {/* Check Frequency */}
          <div className="mb-3">
            <label className="text-xs font-medium text-foreground block mb-1">Check Frequency</label>
            <div className="flex gap-1.5">
              {[
                { value: 'per_feature', label: 'Per Feature' },
                { value: 'every_tool_call', label: 'Every Tool Call' },
                { value: 'never', label: 'Never' },
              ].map((opt) => (
                <Button
                  key={opt.value}
                  variant={commCheckFrequency === opt.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => saveWalkieTalkieSetting({ comm_check_frequency: opt.value })}
                  disabled={isSavingSettings}
                  className="flex-1 text-xs h-7"
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Wait Timeout */}
          <div className="mb-3">
            <label className="text-xs font-medium text-foreground block mb-1">Wait Timeout</label>
            <div className="flex gap-1.5">
              {[30, 60, 120, 300].map((secs) => (
                <Button
                  key={secs}
                  variant={commWaitTimeout === secs ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => saveWalkieTalkieSetting({ comm_wait_timeout: secs })}
                  disabled={isSavingSettings}
                  className="flex-1 text-xs h-7"
                >
                  {secs < 60 ? `${secs}s` : `${secs / 60}m`}
                </Button>
              ))}
            </div>
          </div>

          {/* Auto-Reply */}
          <div className="flex items-center justify-between">
            <label htmlFor="wt-auto-reply" className="text-xs font-medium text-foreground">
              Auto-reply on timeout
            </label>
            <Switch
              id="wt-auto-reply"
              size="sm"
              checked={commAutoReply}
              onCheckedChange={() => saveWalkieTalkieSetting({ comm_auto_reply: !commAutoReply })}
              disabled={isSavingSettings}
            />
          </div>

          <p className="text-[10px] text-muted-foreground mt-2">
            Changes take effect on the next agent session.
          </p>
        </div>
      )}

      {/* Disconnection banner with retry capability */}
      {connectionStatus === 'disconnected' && hasActiveChat && (
        <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-2 text-sm text-destructive flex items-center gap-2">
          <WifiOff size={14} />
          <span className="truncate">{lastError ? `Connection lost: ${lastError.slice(0, 100)}` : 'Connection lost.'}</span>
          <button
            onClick={() => {
              disconnect()
              clearMessages()
              if (effectiveConversationId !== null) {
                start(effectiveConversationId, workingDirectory ?? undefined, conversationContextMode, { effort: effortLevel }, conversationModel, providerProp)
              }
            }}
            className="underline font-medium hover:text-destructive/80 flex-shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {/* Panel label (split-view mode) with per-panel model selector */}
      {panelLabel && (
        <div className={`flex items-center justify-between px-3 py-1.5 text-xs font-bold tracking-wide border-b ${
          panelLabel.includes('RESEARCH')
            ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
            : panelLabel.includes('CODER')
              ? 'bg-cyan-500/10 text-cyan-600 border-cyan-500/20'
              : 'bg-violet-500/10 text-violet-600 border-violet-500/20'
        }`}>
          <span>{panelLabel}</span>
          {/* Per-panel model toggle (split-view only) */}
          {fixedContextMode && onModelChange && (
            <div className="flex rounded-full border border-current/20 overflow-hidden ml-2">
              {(['opus', 'sonnet'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => {
                    onModelChange(m)
                    if (effectiveConversationId) {
                      updateWorkspaceConversation(effectiveConversationId, { model: m })
                        .then(() => queryClient.invalidateQueries({ queryKey: ['workspace'] }))
                        .catch((err) => console.error('Failed to update panel model:', err))
                    }
                  }}
                  className={`px-2 py-0.5 text-[10px] font-semibold transition-all ${
                    preferredModel === m
                      ? m === 'opus'
                        ? 'bg-current/20 text-inherit'
                        : 'bg-violet-500/20 text-violet-600'
                      : 'text-current/40 hover:text-current/70'
                  } ${m === 'opus' ? 'rounded-l-full' : 'rounded-r-full border-l border-current/20'}`}
                  title={`Switch to ${m === 'opus' ? 'Opus 4.6' : 'Sonnet 4.6'}`}
                >
                  {m === 'opus' ? 'Opus' : 'Sonnet'}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Compact control bar: Effort pill + thin context budget bar + message count */}
      {(() => {
        // Effort levels only work on Opus 4.6 — Sonnet ignores them entirely.
        const isOpus1M = conversationContextMode === '1m' && conversationModel === 'opus'
        const effortLabels = { low: 'Low', medium: 'Med', high: 'High' } as const
        const effortUseCases = {
          low: 'Quick lookups, classification, routing, sub-agents',
          medium: 'Agentic coding, tool use, code generation',
          high: 'Complex analysis, nuanced reasoning, quality-critical',
        } as const
        const effortColors = {
          low: 'bg-emerald-500 text-white',
          medium: 'bg-blue-500 text-white',
          high: 'bg-orange-500 text-white',
        } as const
        // Use CURRENT context window utilization from the latest API response,
        // NOT cumulative totals. The API returns how many tokens are in the
        // context window RIGHT NOW (input_tokens + cache_read + cache_create).
        // Fall back to contextBudget if no API data yet.
        const usedTokens = apiTokenTotals.currentContext > 0
          ? apiTokenTotals.currentContext
          : (contextBudget.messageTokens || totalTokens) + contextBudget.summaryTokens
        const barBudget = sessionContextMode === '1m' ? 1_000_000 : 200_000
        const barPercent = barBudget > 0 ? Math.min((usedTokens / barBudget) * 100, 100) : 0
        const isExtendedPricing = barBudget === 1_000_000 && usedTokens > 200_000
        // Color coding: green (safe) → yellow (warning) → orange (caution) → red (danger)
        const barFillColor = barPercent >= 60 ? 'bg-destructive'
          : barPercent >= 50 ? 'bg-red-500'
          : barPercent >= 45 ? 'bg-orange-500'
          : barPercent >= 40 ? 'bg-yellow-500'
          : isExtendedPricing ? 'bg-amber-500'
          : 'bg-primary/50'

        return (
          <div className="flex items-center gap-2 px-3 py-1 border-b border-border">
            {/* Effort pill with dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className={`px-2 py-0.5 text-[10px] font-bold rounded-full shrink-0 transition-opacity ${
                    isOpus1M ? effortColors[conversationEffort] : 'bg-muted text-muted-foreground opacity-40'
                  }`}
                  title={isOpus1M ? effortUseCases[conversationEffort] : 'Effort levels are Opus 4.6 only'}
                >
                  {effortLabels[conversationEffort]}
                  {isOpus1M && <ChevronDown size={8} className="inline ml-0.5 opacity-70" />}
                </button>
              </DropdownMenuTrigger>
              {isOpus1M && (
                <DropdownMenuContent align="start" className="w-64">
                  <DropdownMenuLabel className="text-xs">Anthropic Use Cases</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {(['low', 'medium', 'high'] as const).map((level) => (
                    <DropdownMenuItem
                      key={level}
                      className={`gap-2 text-xs cursor-default ${conversationEffort === level ? 'bg-accent' : ''}`}
                      onSelect={(e) => e.preventDefault()}
                    >
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                        level === 'low' ? 'bg-emerald-500' : level === 'medium' ? 'bg-blue-500' : 'bg-orange-500'
                      }`} />
                      <div className="flex flex-col gap-0.5">
                        <span className="font-semibold">{effortLabels[level]}</span>
                        <span className="text-[10px] text-muted-foreground">{effortUseCases[level]}</span>
                      </div>
                      {conversationEffort === level && <Check size={12} className="ml-auto text-primary" />}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              )}
            </DropdownMenu>

            {/* Thin inline context budget bar */}
            <div className="flex-1 flex items-center gap-2 min-w-0">
              <div className="flex-1 relative h-2 rounded-full bg-muted overflow-hidden">
                {/* Fill */}
                <div
                  className={`absolute top-0 left-0 h-full rounded-full transition-all duration-500 ease-out ${barFillColor} ${barPercent >= 50 ? 'animate-pulse' : ''}`}
                  style={{ width: `${barPercent}%` }}
                />
                {/* 200K pricing cliff marker on 1M panels */}
                {barBudget === 1_000_000 && (
                  <div
                    className={`absolute top-0 h-full w-0.5 z-10 ${
                      isExtendedPricing ? 'bg-amber-500' : 'bg-amber-500/40'
                    }`}
                    style={{ left: '20%' }}
                    title="200K pricing threshold"
                  />
                )}
                {/* Streaming shimmer */}
                {isLoading && (
                  <div className="absolute top-0 right-0 h-full w-8 animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                )}
              </div>
              {/* Usage text beside the bar */}
              <span className="text-[10px] font-mono text-muted-foreground whitespace-nowrap tabular-nums shrink-0">
                {barPercent < 1 && barPercent > 0 ? barPercent.toFixed(1) : Math.round(barPercent)}% · {formatTokenCount(usedTokens)}/{formatTokenCount(barBudget)}
              </span>
            </div>

            {/* Message count */}
            <span className="text-[10px] text-muted-foreground/60 tabular-nums whitespace-nowrap shrink-0">
              {contextBudget.messageCount} msg{contextBudget.messageCount !== 1 ? 's' : ''}
            </span>
          </div>
        )
      })()}

      {/* Usage dashboard */}
      <UsageDashboard
        conversationId={conversationId ?? activeConversationId}
        contextMode={sessionContextMode}
        model={conversationModel}
      />

      {/* Auto-summary pin */}
      <AutoSummaryPin
        summary={summary?.summary ?? null}
        updatedAt={summary?.created_at ?? null}
        messagesCovered={summary?.message_count ?? null}
        onRegenerate={() => regenerateMutation.mutate()}
        isRegenerating={regenerateMutation.isPending}
      />


      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto"
        onScroll={handleScroll}
      >
        {showEmptyState ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <MessageSquare size={48} className="text-muted-foreground/30" />
            <div className="text-center">
              {pendingModel && newChatKey && newChatKey > 0 ? (
                <>
                  <h2 className="text-lg font-semibold text-foreground mb-2">
                    New Chat — {pendingModel === 'sonnet' ? 'Sonnet 4.6' : 'Opus 4.6'} ({pendingContextModeProp === '200k' ? '200K' : '1M'})
                  </h2>
                  <p className="text-sm mb-6 max-w-sm">
                    Type your message below to start this conversation.
                  </p>
                </>
              ) : (
                <>
                  <h2 className="text-lg font-semibold text-foreground mb-2">
                    No conversations yet
                  </h2>
                  <p className="text-sm mb-6 max-w-sm">
                    Start your first conversation to brainstorm ideas, explore concepts, or get help with your projects.
                  </p>
                </>
              )}
              <p className="text-xs text-muted-foreground mb-4">
                Type a message below and press Enter to begin.
              </p>
            </div>
          </div>
        ) : reconnectionExhausted && displayMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <WifiOff size={48} className="text-muted-foreground/30" />
            <div className="text-center max-w-md">
              <h2 className="text-lg font-semibold text-foreground mb-2">
                Connection Failed
              </h2>
              {lastError ? (
                <div className="mb-4 p-3 bg-destructive/5 border border-destructive/20 rounded-md text-sm text-left">
                  <p className="font-medium text-destructive mb-1">Error details:</p>
                  <p className="text-muted-foreground">{typeof lastError === 'string' ? lastError : String(lastError)}</p>
                </div>
              ) : (
                <p className="text-sm mb-4">
                  Could not connect to the workspace server. The server may be restarting or unavailable.
                </p>
              )}
              <p className="text-xs text-muted-foreground mb-4">
                If you&apos;re seeing this repeatedly, the Claude API may be rate-limited. Wait a few minutes and try again.
              </p>
              <div className="flex gap-2 justify-center">
                <Button
                  onClick={() => {
                    disconnect()
                    clearMessages()
                    if (effectiveConversationId !== null) {
                      start(effectiveConversationId, workingDirectory ?? undefined, conversationContextMode, { effort: effortLevel }, conversationModel, providerProp)
                    }
                  }}
                >
                  Retry Connection
                </Button>
                {onNewConversation && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      disconnect()
                      clearMessages()
                      onNewConversation()
                    }}
                  >
                    Back to Conversations
                  </Button>
                )}
              </div>
            </div>
          </div>
        ) : isLoadingConversation ? (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            <div className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              <span>Loading conversation...</span>
            </div>
          </div>
        ) : (
          <div className="py-4">
            {displayMessages.map((message) => {
              // For assistant messages, extract structured blocks and strip
              // them from the content so tags are not rendered twice.
              let hasBlocks = false
              let renderedMessage = message
              try {
                hasBlocks =
                  message.role === 'assistant' &&
                  parseStructuredBlocks(message.content).length > 0
                if (hasBlocks) {
                  renderedMessage = { ...message, content: stripStructuredBlocks(message.content) }
                }
              } catch {
                // Malformed content — render as-is without crashing
              }

              return (
                <div key={message.id ?? generateId()}>
                  {hasBlocks && (
                    <div className="px-4 py-1">
                      <AgentNotifications content={message.content} />
                    </div>
                  )}
                  <ChatMessage
                    message={renderedMessage}
                    onCopyToPassoff={onCopyToPassoff}
                    onSaveToLibrary={(content) => setSaveToLibraryContent(content)}
                  />
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Loading indicator */}
      {isLoading && displayMessages.length > 0 && !agentWaiting && (
        <div className="px-4 py-2 border-t border-border bg-background">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
            </span>
            <span>Agent working...</span>
            <ElapsedTimer active={isLoading} />
          </div>
        </div>
      )}

      {/* Countdown timer bar: shown when agent is waiting for user input */}
      <CountdownTimerBar
        active={agentWaiting}
        totalSeconds={commWaitTimeout}
        autoReply={commAutoReply}
        onKeepGoing={handleTimerKeepGoing}
        onTimeout={handleTimerTimeout}
      />

      {/* Agent waiting question display */}
      {agentWaiting && agentWaitingQuestion && (
        <div className="px-4 py-2 bg-amber-50 dark:bg-amber-950/30 border-t border-amber-300 dark:border-amber-700/50 text-sm text-amber-800 dark:text-amber-300">
          <span className="font-medium">Agent asks: </span>
          <span className="line-clamp-2">{agentWaitingQuestion}</span>
        </div>
      )}

      {/* Walkie-talkie input bar: shown when agent is actively working */}
      {walkieTalkieVisible && (
        <div className="flex items-center gap-2 px-4 py-2 bg-amber-50 dark:bg-amber-950/20 border-t border-amber-300 dark:border-amber-700/40 border-l-[3px] border-l-amber-500">
          <Radio size={16} className="flex-shrink-0 text-amber-600 dark:text-amber-400" />
          <input
            ref={walkieTalkieInputRef}
            type="text"
            value={walkieTalkieInput}
            onChange={(e) => setWalkieTalkieInput(e.target.value)}
            onKeyDown={handleWalkieTalkieKeyDown}
            placeholder="Send message to working agent..."
            className="flex-1 h-8 rounded-md border border-amber-300 dark:border-amber-700 bg-white dark:bg-amber-950/30 px-2.5 text-sm text-foreground placeholder:text-amber-400 dark:placeholder:text-amber-600 outline-none ring-amber-400 focus:ring-1"
          />
          {walkieTalkieSent ? (
            <span className="flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400 animate-pulse">
              <Check size={14} />
              Sent!
            </span>
          ) : (
            <Button
              size="sm"
              onClick={handleWalkieTalkieSend}
              disabled={!walkieTalkieInput.trim()}
              className="h-8 px-3 bg-amber-500 hover:bg-amber-600 text-white text-xs font-medium"
            >
              <Send size={14} />
            </Button>
          )}
        </div>
      )}

      {/* Injection indicator */}
      {pendingInjection && (
        <div className="flex items-center gap-2 px-4 py-2 bg-muted border-t border-border text-sm text-muted-foreground">
          <ArrowDownToLine size={14} />
          <span>
            Injecting {pendingInjection.messages.length} message{pendingInjection.messages.length !== 1 ? 's' : ''} from &quot;{pendingInjection.sourceTitle}&quot;
          </span>
          <button
            onClick={() => setPendingInjection(null)}
            className="ml-auto text-muted-foreground hover:text-foreground"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Input area */}
      <div
        className={`border-t border-border p-4 bg-card transition-colors ${isDragging ? 'ring-2 ring-primary bg-primary/5' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Drag overlay indicator */}
        {isDragging && (
          <div className="flex items-center justify-center py-3 mb-3 border-2 border-dashed border-primary rounded-md text-sm text-primary">
            <ImagePlus size={16} className="mr-2" />
            Drop files or images here
          </div>
        )}

        {/* Pending images preview */}
        {pendingImages.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {pendingImages.map((img) => (
              <div key={img.id} className="relative group">
                <img
                  src={img.previewUrl}
                  alt={img.filename}
                  className="w-16 h-16 object-cover rounded border border-border"
                />
                <button
                  onClick={() => setPendingImages(prev => prev.filter(i => i.id !== img.id))}
                  className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center text-[10px] opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={10} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Pending files preview */}
        {pendingFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {pendingFiles.map((file, i) => (
              <div key={`${file.name}-${i}`} className="flex items-center gap-1.5 px-2 py-1 bg-muted rounded text-xs text-foreground group">
                <Paperclip size={12} />
                <span className="truncate max-w-[120px]">{file.name}</span>
                <button
                  onClick={() => setPendingFiles(prev => prev.filter((_, idx) => idx !== i))}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Attached library files preview */}
        {attachedLibraryFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {attachedLibraryFiles.map((file) => (
              <div key={file.id} className="flex items-center gap-1.5 px-2 py-1 bg-primary/10 border border-primary/20 rounded text-xs text-foreground group">
                <BookOpen size={12} className="text-primary" />
                <span className="truncate max-w-[120px]">{file.display_name || file.filename}</span>
                <button
                  onClick={() => setAttachedLibraryFiles(prev => prev.filter(f => f.id !== file.id))}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          {/* File upload button */}
          <Button
            variant="ghost"
            size="sm"
            className="h-[44px] px-2 text-muted-foreground hover:text-foreground"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || isLoadingConversation}
            title="Attach file"
          >
            <Paperclip size={18} />
          </Button>

          {/* Image upload button */}
          <Button
            variant="ghost"
            size="sm"
            className="h-[44px] px-2 text-muted-foreground hover:text-foreground"
            onClick={() => imageInputRef.current?.click()}
            disabled={isLoading || isLoadingConversation}
            title="Attach image"
          >
            <ImagePlus size={18} />
          </Button>

          {/* Attach from Library button */}
          <Button
            variant="ghost"
            size="sm"
            className={`h-[44px] px-2 ${attachedLibraryFiles.length > 0 ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
            onClick={() => setShowLibraryPicker(true)}
            disabled={isLoading || isLoadingConversation}
            title={attachedLibraryFiles.length > 0 ? `${attachedLibraryFiles.length} library file(s) attached` : 'Attach from Library'}
          >
            <BookOpen size={18} />
            {attachedLibraryFiles.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                {attachedLibraryFiles.length}
              </span>
            )}
          </Button>

          {/* Hidden file inputs */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => {
              const files = Array.from(e.target.files || [])
              if (files.length > 0) processFiles(files)
              e.target.value = '' // Reset so same file can be selected again
            }}
          />
          <input
            ref={imageInputRef}
            type="file"
            multiple
            accept="image/jpeg,image/png,image/gif,image/webp"
            className="hidden"
            onChange={(e) => {
              const files = Array.from(e.target.files || [])
              if (files.length > 0) processImageFiles(files)
              e.target.value = ''
            }}
          />

          <textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value)
              // Auto-expand: reset height then set to scrollHeight (capped by max-h)
              const el = e.target
              el.style.height = 'auto'
              el.style.height = `${Math.min(el.scrollHeight, 240)}px`
            }}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder={isLoading && firstMessageSent ? "Type to send via walkie-talkie..." : "Ask anything... (paste images with Ctrl+V)"}
            disabled={isLoadingConversation || (isLoading && !firstMessageSent)}
            className="flex-1 resize-y min-h-[44px] max-h-[240px] rounded-md border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none ring-ring focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
            rows={1}
          />
          {isLoading ? (
            <div className="flex gap-1">
              {firstMessageSent && (
                <Button
                  onClick={handleSend}
                  disabled={!inputValue.trim()}
                  title="Send via walkie-talkie (no extra API cost)"
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                >
                  <Send size={16} />
                </Button>
              )}
              <Button
                onClick={handleEndSession}
                title="End session gracefully (writes handoff)"
                className="bg-orange-600 hover:bg-orange-700 text-white"
              >
                <LogOut size={16} />
              </Button>
              <Button
                onClick={cancelSession}
                title="Force stop agent"
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                <Square size={16} className="fill-current" />
              </Button>
            </div>
          ) : (
            <Button
              onClick={handleSend}
              disabled={(!inputValue.trim() && pendingImages.length === 0 && pendingFiles.length === 0) || isLoadingConversation}
              title={fixedContextMode === '200k' ? 'Send (Subscription)' : fixedContextMode === '1m' ? 'Send (API)' : 'Send message'}
              className={
                panelLabel?.includes('RESEARCH')
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  : panelLabel?.includes('CODER')
                    ? 'bg-cyan-600 hover:bg-cyan-700 text-white'
                    : panelLabel?.includes('PRD')
                      ? 'bg-violet-600 hover:bg-violet-700 text-white'
                      : undefined
              }
            >
              <Send size={18} />
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Enter to send, Shift+Enter for new line. Drag &amp; drop or paste images.
        </p>
      </div>

      {/* Fork modal */}
      {showForkModal && effectiveConversationId && (
        <ChatForkModal
          isOpen={showForkModal}
          onClose={() => setShowForkModal(false)}
          conversationId={effectiveConversationId}
          conversationTitle={effectiveTitle || 'Untitled'}
          messages={forkableMessages}
          onForkCreated={handleForkCreated}
        />
      )}

      {/* Inject modal */}
      {showInjectModal && effectiveConversationId && (
        <InjectFromChatModal
          isOpen={showInjectModal}
          onClose={() => setShowInjectModal(false)}
          currentConversationId={effectiveConversationId}
          onInject={handleInject}
        />
      )}

      {/* Save to Library modal */}
      {saveToLibraryContent !== null && (
        <SaveToLibraryModal
          open
          onClose={() => setSaveToLibraryContent(null)}
          content={saveToLibraryContent}
        />
      )}

      {/* Library Picker modal */}
      {showLibraryPicker && (
        <LibraryPickerModal
          open
          onClose={() => setShowLibraryPicker(false)}
          onAttach={(files) => {
            setAttachedLibraryFiles(files)
            setShowLibraryPicker(false)
          }}
          selectedFileIds={attachedLibraryFiles.map(f => f.id)}
        />
      )}
      </div>{/* end main chat content */}
    </div>
  )
}
