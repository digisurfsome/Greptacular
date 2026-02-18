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
} from 'lucide-react'
import { useWorkspaceChat } from '@/hooks/useWorkspaceChat'
import { useWorkspaceConversation } from '@/hooks/useWorkspaceConversations'
import { ChatMessage } from '@/components/ChatMessage'
import { isSubmitEnter } from '@/lib/keyboard'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getWorkspaceSummary, regenerateWorkspaceSummary, exportConversationMarkdown, updateWorkspaceConversation } from '@/lib/api'
import { WorkspaceChatHeader } from './WorkspaceChatHeader'
import { EnhancedContextBudgetBar, getContextWarningClass } from './EnhancedContextBudgetBar'
import { UsageDashboard } from './UsageDashboard'
import { AutoSummaryPin } from './AutoSummaryPin'
import { ChatForkModal } from './ChatForkModal'
import { InjectFromChatModal } from './InjectFromChatModal'
import CostControls, { loadCostSettings, type CostSettings } from './CostControls'
import type { ChatMessage as ChatMessageType, WorkspaceMessage, PendingInjection, ImageAttachment } from '@/lib/types'

const DRAFT_KEY_PREFIX = 'workspace-draft-'

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
}: WorkspaceChatProps): React.JSX.Element {
  const [inputValue, setInputValue] = useState('')
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const internalInputRef = useRef<HTMLTextAreaElement>(null)
  const inputRef = externalInputRef ?? internalInputRef
  const lastConversationIdRef = useRef<number | null | undefined>(undefined)
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false)
  const [showForkModal, setShowForkModal] = useState(false)
  const [showInjectModal, setShowInjectModal] = useState(false)
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  const [pendingImages, setPendingImages] = useState<ImageAttachment[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [contextToast, setContextToast] = useState<string | null>(null)
  const contextToastTimerRef = useRef<number | null>(null)

  // Context mode: "1m" (1,000,000 tokens with beta) or "200k" (200,000 tokens standard).
  // When fixedContextMode is set (split-view), the mode is locked and the toggle is hidden.
  // Otherwise, it's persisted to localStorage and takes effect on the NEXT session start.
  //
  // pendingContextMode = what the user WANTS for the next session (persisted to localStorage).
  // sessionContextMode = what the CURRENT session is actually running on (drives gauge + button).
  // These diverge when the user toggles mid-chat.  They re-sync when a new session starts.
  const pendingContextModeRef = useRef<'1m' | '200k'>(
    fixedContextMode ?? ((localStorage.getItem('workspace-context-mode') as '1m' | '200k') || '1m')
  )
  const [sessionContextMode, setSessionContextMode] = useState<'1m' | '200k'>(
    fixedContextMode ?? pendingContextModeRef.current
  )

  // Keep pendingContextModeRef in sync when fixedContextMode changes
  useEffect(() => {
    if (fixedContextMode) {
      pendingContextModeRef.current = fixedContextMode
      setSessionContextMode(fixedContextMode)
    }
  }, [fixedContextMode])

  // Cost control settings -- persisted to localStorage, sent on session start.
  const [costSettings, setCostSettings] = useState<CostSettings>(loadCostSettings)

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
    start,
    sendMessage,
    disconnect,
    clearMessages,
  } = useWorkspaceChat({ onError: handleError })

  // REST query for initial messages when resuming a conversation
  const { data: conversationDetail, isLoading: isLoadingConversation } =
    useWorkspaceConversation(conversationId)

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
    }

    // Start/resume the selected conversation, passing the working directory
    // so the agent session uses the repo clone as its cwd.
    // Sync the session mode to the pending preference at session start.
    if (conversationId !== null) {
      const modeForSession = pendingContextModeRef.current
      setSessionContextMode(modeForSession)
      start(conversationId, workingDirectory ?? undefined, modeForSession, costSettings as unknown as Record<string, unknown>)
    }
  }, [conversationId, isLoadingConversation, activeConversationId, start, disconnect, clearMessages, workingDirectory, costSettings])

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

  // Detect response completion (isLoading true→false) for auto-forward
  const prevLoadingRef = useRef(false)
  useEffect(() => {
    if (prevLoadingRef.current && !isLoading && onResponseComplete) {
      const lastMessage = liveMessages[liveMessages.length - 1]
      if (lastMessage?.role === 'assistant' && lastMessage.content) {
        onResponseComplete(lastMessage.content)
      }
    }
    prevLoadingRef.current = isLoading
  }, [isLoading, liveMessages, onResponseComplete])

  // Focus input when not loading
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus()
    }
  }, [isLoading, inputRef])

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
      start(undefined, workingDirectory ?? undefined, pendingContextModeRef.current, costSettings as unknown as Record<string, unknown>)
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
      timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
    }))
  }, [conversationDetail])

  // Merge initial (REST) messages with live (WebSocket) messages, deduplicating
  const displayMessages: ChatMessageType[] = useMemo(() => {
    if (initialMessages.length === 0) return liveMessages
    if (liveMessages.length === 0) return initialMessages

    const seen = new Map<string, ChatMessageType>()
    for (const msg of initialMessages) {
      seen.set(dedupKey(msg), msg)
    }
    for (const msg of liveMessages) {
      // Live messages take precedence (may have streaming state)
      seen.set(dedupKey(msg), msg)
    }
    return Array.from(seen.values())
  }, [initialMessages, liveMessages])

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

  // Send handler
  const handleSend = useCallback(async () => {
    let content = inputValue.trim()
    if (!content && pendingImages.length === 0 && pendingFiles.length === 0) return
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

    // If no conversation yet, start a new one first. The hook will queue
    // the message and dispatch it once the session is ready.
    // Pass workingDirectory so the new session uses the selected repo.
    if (conversationId === null && activeConversationId === null) {
      start(undefined, workingDirectory ?? undefined, pendingContextModeRef.current, costSettings as unknown as Record<string, unknown>)
    }
    sendMessage(content, attachments)

    setInputValue('')
    setPendingImages([])
    setPendingFiles([])
    // Clear draft after sending
    const effectiveId = conversationId ?? activeConversationId
    if (effectiveId) {
      localStorage.removeItem(`${DRAFT_KEY_PREFIX}${effectiveId}`)
    }
  }, [inputValue, isLoading, conversationId, activeConversationId, start, sendMessage, workingDirectory, pendingImages, pendingFiles, sessionContextMode, costSettings])

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
    queryClient.invalidateQueries({ queryKey: ['workspace-conversations'] })
  }, [onConversationCreated, queryClient])

  const handleInject = useCallback((injection: PendingInjection) => {
    setPendingInjection(injection)
    setShowInjectModal(false)
  }, [setPendingInjection])

  return (
    <div className={`flex flex-col h-full bg-background transition-colors duration-500 ${getContextWarningClass(usagePercent)}`}>
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
          />
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
                start(effectiveConversationId, workingDirectory ?? undefined, pendingContextModeRef.current, costSettings as unknown as Record<string, unknown>)
              }
            }}
            className="underline font-medium hover:text-destructive/80 flex-shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {/* Panel label (split-view mode) */}
      {panelLabel && (
        <div className={`flex items-center justify-center px-3 py-1.5 text-xs font-bold tracking-wide border-b ${
          panelLabel.includes('RESEARCH')
            ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
            : panelLabel.includes('CODER')
              ? 'bg-cyan-500/10 text-cyan-600 border-cyan-500/20'
              : 'bg-violet-500/10 text-violet-600 border-violet-500/20'
        }`}>
          {panelLabel}
        </div>
      )}

      {/* Context mode toggle + budget bar */}
      <div className="flex items-center border-b border-border bg-card/80">
        <div className="flex-1 border-b-0 [&>div]:border-b-0">
          <EnhancedContextBudgetBar
            totalBudget={sessionContextMode === '1m' ? 1_000_000 : 200_000}
            messageTokens={contextBudget.messageTokens || totalTokens}
            summaryTokens={contextBudget.summaryTokens}
            messageCount={contextBudget.messageCount}
            isStreaming={isLoading}
            preferredModel={
              panelLabel?.includes('Sonnet') ? 'sonnet'
                : panelLabel?.includes('Opus') ? 'opus'
                  : undefined
            }
          />
        </div>
        {/* Hide toggle when mode is fixed (split-view panels) */}
        {!fixedContextMode && <button
          onClick={() => {
            const newMode = pendingContextModeRef.current === '1m' ? '200k' : '1m'
            pendingContextModeRef.current = newMode
            localStorage.setItem('workspace-context-mode', newMode)
            // Show toast — button and gauge stay on the ACTIVE mode
            const label = newMode === '1m' ? '1M' : '200K'
            setContextToast(`Next conversation will use ${label} context window`)
            // Clear any existing timer and set new auto-dismiss
            if (contextToastTimerRef.current) clearTimeout(contextToastTimerRef.current)
            contextToastTimerRef.current = window.setTimeout(() => {
              setContextToast(null)
              contextToastTimerRef.current = null
            }, 8000)
          }}
          className={`flex-shrink-0 mr-4 text-[10px] font-mono font-bold px-2 py-0.5 rounded border transition-colors ${
            sessionContextMode === '1m'
              ? 'bg-primary/10 text-primary border-primary/30'
              : 'bg-muted text-muted-foreground border-border'
          }`}
          title={`Context window: ${sessionContextMode === '1m' ? '1,000,000' : '200,000'} tokens. Click to switch. Takes effect on next session.`}
        >
          {sessionContextMode === '1m' ? '1M ctx' : '200K ctx'}
        </button>}
      </div>

      {/* Context mode toast notification */}
      {contextToast && (
        <div className="flex items-center justify-between px-4 py-2 bg-primary/10 border-b border-primary/20 text-sm text-primary animate-slide-in">
          <span>{contextToast}</span>
          <button
            onClick={() => {
              setContextToast(null)
              if (contextToastTimerRef.current) {
                clearTimeout(contextToastTimerRef.current)
                contextToastTimerRef.current = null
              }
            }}
            className="ml-3 text-primary/60 hover:text-primary text-xs"
          >
            dismiss
          </button>
        </div>
      )}

      {/* Cost controls — user-adjustable "stick shift" for API spend */}
      <CostControls settings={costSettings} onChange={setCostSettings} />

      {/* Usage dashboard */}
      <UsageDashboard
        conversationId={conversationId ?? activeConversationId}
        contextMode={sessionContextMode}
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
              <h2 className="text-lg font-semibold text-foreground mb-2">
                No conversations yet
              </h2>
              <p className="text-sm mb-6 max-w-sm">
                Start your first conversation to brainstorm ideas, explore concepts, or get help with your projects.
              </p>
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
                  <p className="text-muted-foreground">{lastError}</p>
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
                      start(effectiveConversationId, workingDirectory ?? undefined, pendingContextModeRef.current, costSettings as unknown as Record<string, unknown>)
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
            {displayMessages.map((message) => (
              <ChatMessage
                key={message.id ?? generateId()}
                message={message}
                onCopyToPassoff={onCopyToPassoff}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Loading indicator */}
      {isLoading && displayMessages.length > 0 && (
        <div className="px-4 py-2 border-t border-border bg-background">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Loader2 size={16} className="animate-spin" />
            <span>Thinking...</span>
          </div>
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
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder="Ask anything... (paste images with Ctrl+V)"
            disabled={isLoading || isLoadingConversation}
            className="flex-1 resize-none min-h-[44px] max-h-[120px] rounded-md border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none ring-ring focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
            rows={1}
          />
          <Button
            onClick={handleSend}
            disabled={(!inputValue.trim() && pendingImages.length === 0 && pendingFiles.length === 0) || isLoading || isLoadingConversation}
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
            {isLoading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </Button>
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
    </div>
  )
}
