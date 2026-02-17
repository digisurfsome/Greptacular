/**
 * InjectFromChatModal - Two-step modal for injecting messages from another conversation.
 *
 * Step 1: Select a source conversation from a searchable list.
 * Step 2: Select individual messages to inject via checkboxes.
 */

import { useState, useCallback, useEffect, useMemo } from 'react'
import { Loader2, ArrowLeft, ArrowDownToLine, Search, CheckSquare, Square } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { listWorkspaceConversations, getConversationMessages } from '@/lib/api'
import type { WorkspaceConversation, WorkspaceMessage, PendingInjection } from '@/lib/types'

interface InjectFromChatModalProps {
  isOpen: boolean
  onClose: () => void
  currentConversationId: number
  onInject: (injection: PendingInjection) => void
}

/** Two-step modal for selecting and injecting messages from another conversation. */
export function InjectFromChatModal({
  isOpen,
  onClose,
  currentConversationId,
  onInject,
}: InjectFromChatModalProps): React.JSX.Element {
  const [step, setStep] = useState<1 | 2>(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [conversations, setConversations] = useState<WorkspaceConversation[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null)
  const [selectedSourceTitle, setSelectedSourceTitle] = useState('')
  const [sourceMessages, setSourceMessages] = useState<WorkspaceMessage[]>([])
  const [selectedMessageIds, setSelectedMessageIds] = useState<Set<number>>(new Set())
  const [isLoadingConvs, setIsLoadingConvs] = useState(false)
  const [isLoadingMsgs, setIsLoadingMsgs] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load conversations on open
  useEffect(() => {
    if (!isOpen) return
    setStep(1)
    setSearchQuery('')
    setSelectedSourceId(null)
    setSourceMessages([])
    setSelectedMessageIds(new Set())
    setError(null)

    setIsLoadingConvs(true)
    listWorkspaceConversations()
      .then((data) => setConversations(data))
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load conversations'))
      .finally(() => setIsLoadingConvs(false))
  }, [isOpen])

  // Filter conversations excluding current, matching search
  const filteredConversations = useMemo(() => {
    const filtered = conversations.filter((c) => c.id !== currentConversationId)
    if (!searchQuery.trim()) return filtered
    const term = searchQuery.trim().toLowerCase()
    return filtered.filter((c) =>
      (c.title ?? 'Untitled').toLowerCase().includes(term),
    )
  }, [conversations, currentConversationId, searchQuery])

  // Select a source conversation and load its messages
  const handleSelectSource = useCallback(async (conv: WorkspaceConversation) => {
    setSelectedSourceId(conv.id)
    setSelectedSourceTitle(conv.title ?? 'Untitled')
    setIsLoadingMsgs(true)
    setError(null)
    try {
      const result = await getConversationMessages(conv.id, 100, 0)
      setSourceMessages(result.messages)
      setSelectedMessageIds(new Set())
      setStep(2)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load messages')
    } finally {
      setIsLoadingMsgs(false)
    }
  }, [])

  const handleToggleMessage = useCallback((msgId: number) => {
    setSelectedMessageIds((prev) => {
      const next = new Set(prev)
      if (next.has(msgId)) {
        next.delete(msgId)
      } else {
        next.add(msgId)
      }
      return next
    })
  }, [])

  const handleSelectAll = useCallback(() => {
    if (selectedMessageIds.size === sourceMessages.length) {
      setSelectedMessageIds(new Set())
    } else {
      setSelectedMessageIds(new Set(sourceMessages.map((m) => m.id)))
    }
  }, [selectedMessageIds.size, sourceMessages])

  const handleInject = useCallback(() => {
    const selected = sourceMessages.filter((m) => selectedMessageIds.has(m.id))
    onInject({
      sourceTitle: selectedSourceTitle,
      sourceConversationId: selectedSourceId!,
      messages: selected.map((m) => ({ role: m.role, content: m.content })),
    })
  }, [sourceMessages, selectedMessageIds, selectedSourceTitle, selectedSourceId, onInject])

  const allSelected = sourceMessages.length > 0 && selectedMessageIds.size === sourceMessages.length

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ArrowDownToLine size={18} className="text-primary" />
            {step === 1 ? 'Select Source Conversation' : 'Select Messages to Inject'}
          </DialogTitle>
        </DialogHeader>

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        {step === 1 ? (
          <>
            {/* Search filter */}
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="pl-9"
              />
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto max-h-[40vh] border border-border rounded-md">
              {isLoadingConvs ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
                  <Loader2 size={16} className="animate-spin mr-2" />
                  Loading...
                </div>
              ) : filteredConversations.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No other conversations found.
                </p>
              ) : (
                filteredConversations.map((conv) => (
                  <button
                    key={conv.id}
                    type="button"
                    onClick={() => handleSelectSource(conv)}
                    className="w-full flex items-center justify-between px-3 py-2.5 text-left border-b border-border last:border-b-0 hover:bg-muted transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground truncate">
                        {conv.title ?? 'Untitled'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {conv.message_count} messages
                      </p>
                    </div>
                  </button>
                ))
              )}
            </div>
          </>
        ) : (
          <>
            {/* Message selection */}
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                {selectedMessageIds.size} of {sourceMessages.length} selected
              </p>
              <Button variant="ghost" size="sm" onClick={handleSelectAll}>
                {allSelected ? <CheckSquare size={14} className="mr-1" /> : <Square size={14} className="mr-1" />}
                {allSelected ? 'Deselect All' : 'Select All'}
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto max-h-[40vh] border border-border rounded-md">
              {isLoadingMsgs ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
                  <Loader2 size={16} className="animate-spin mr-2" />
                  Loading messages...
                </div>
              ) : (
                sourceMessages.map((msg) => {
                  const roleLabel = msg.role === 'user' ? 'User' : 'Assistant'
                  const preview = msg.content.length > 100
                    ? msg.content.slice(0, 100) + '...'
                    : msg.content
                  return (
                    <label
                      key={msg.id}
                      className={`flex items-start gap-3 px-3 py-2 cursor-pointer border-b border-border last:border-b-0 transition-colors ${
                        selectedMessageIds.has(msg.id) ? 'bg-accent' : 'hover:bg-muted'
                      }`}
                    >
                      <div className="pt-0.5">
                        <Checkbox
                          checked={selectedMessageIds.has(msg.id)}
                          onCheckedChange={() => handleToggleMessage(msg.id)}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-medium text-muted-foreground">
                          [{roleLabel}]
                        </span>
                        <p className="text-sm text-foreground">
                          {preview}
                        </p>
                      </div>
                    </label>
                  )
                })
              )}
            </div>
          </>
        )}

        <DialogFooter>
          {step === 2 && (
            <Button
              variant="outline"
              onClick={() => setStep(1)}
              className="mr-auto"
            >
              <ArrowLeft size={14} className="mr-1" />
              Back
            </Button>
          )}
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          {step === 2 && (
            <Button
              onClick={handleInject}
              disabled={selectedMessageIds.size === 0}
            >
              <ArrowDownToLine size={14} className="mr-1" />
              Inject ({selectedMessageIds.size})
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
