/**
 * ChatForkModal - Modal for forking a conversation from a specific message.
 *
 * Displays a scrollable list of messages with radio buttons to select the
 * fork point. On fork, calls the backend API and navigates to the new
 * conversation.
 */

import { useState, useCallback } from 'react'
import { Loader2, GitFork } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { forkConversation } from '@/lib/api'
import type { WorkspaceMessage } from '@/lib/types'

interface ChatForkModalProps {
  isOpen: boolean
  onClose: () => void
  conversationId: number
  conversationTitle: string
  messages: WorkspaceMessage[]
  onForkCreated: (newId: number) => void
}

/** Modal for forking a conversation from a specific message point. */
export function ChatForkModal({
  isOpen,
  onClose,
  conversationId,
  conversationTitle,
  messages,
  onForkCreated,
}: ChatForkModalProps): React.JSX.Element {
  const lastMessageId = messages.length > 0 ? messages[messages.length - 1].id : null
  const [selectedMessageId, setSelectedMessageId] = useState<number | null>(lastMessageId)
  const [isForking, setIsForking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFork = useCallback(async () => {
    setIsForking(true)
    setError(null)
    try {
      const result = await forkConversation(conversationId, selectedMessageId)
      onForkCreated(result.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Fork failed')
    } finally {
      setIsForking(false)
    }
  }, [conversationId, selectedMessageId, onForkCreated])

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitFork size={18} className="text-primary" />
            Fork Conversation
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            Create a branch from &quot;{conversationTitle}&quot;
          </p>
        </DialogHeader>

        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            No messages to fork.
          </p>
        ) : (
          <>
            <p className="text-xs text-muted-foreground">
              Select fork point:
            </p>
            <div className="flex-1 overflow-y-auto max-h-[40vh] border border-border rounded-md">
              {messages.map((msg, idx) => {
                const roleLabel = msg.role === 'user' ? 'User' : 'Assistant'
                const preview = msg.content.length > 80
                  ? msg.content.slice(0, 80) + '...'
                  : msg.content
                return (
                  <label
                    key={msg.id}
                    className={`flex items-start gap-3 px-3 py-2 cursor-pointer transition-colors border-b border-border last:border-b-0 ${
                      selectedMessageId === msg.id
                        ? 'bg-accent'
                        : 'hover:bg-muted'
                    }`}
                  >
                    <input
                      type="radio"
                      name="fork-point"
                      checked={selectedMessageId === msg.id}
                      onChange={() => setSelectedMessageId(msg.id)}
                      className="mt-1 accent-primary"
                    />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-medium text-muted-foreground">
                        [{roleLabel}]
                      </span>
                      <p className="text-sm text-foreground truncate">
                        {preview}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">
                      #{idx + 1}
                    </span>
                  </label>
                )
              })}
            </div>
            <p className="text-xs text-muted-foreground">
              Messages after the selected point will not be copied.
            </p>
          </>
        )}

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isForking}>
            Cancel
          </Button>
          <Button
            onClick={handleFork}
            disabled={isForking || messages.length === 0}
          >
            {isForking ? (
              <>
                <Loader2 size={14} className="animate-spin mr-1" />
                Forking...
              </>
            ) : (
              <>
                <GitFork size={14} className="mr-1" />
                Fork
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
