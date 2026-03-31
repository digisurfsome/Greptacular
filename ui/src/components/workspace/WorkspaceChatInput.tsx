/**
 * WorkspaceChatInput — Memoized input component for WorkspaceChat.
 *
 * Extracted to prevent re-renders from WebSocket message state changes
 * from freezing the typing experience. React.memo ensures this only
 * re-renders when its own props change (typing, loading state, etc.),
 * NOT when messages/tokenLog/tool_call events arrive.
 */

import React, { useState, useCallback, useEffect, useImperativeHandle } from 'react'
import { Send, Paperclip, ImagePlus, BookOpen, LogOut, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'

/** Handle exposed to parent via ref — lets parent read/set input without owning state */
export interface WorkspaceChatInputHandle {
  getValue: () => string
  setValue: (v: string) => void
  clear: () => void
}

interface WorkspaceChatInputProps {
  /** Called when user presses Enter or clicks Send */
  onSend: (text: string) => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void
  onPaste: (e: React.ClipboardEvent) => void
  placeholder: string
  disabled: boolean
  isWalkieTalkieMode: boolean
  isLoading: boolean
  firstMessageSent: boolean
  onEndSession: () => void
  onCancelSession: () => void
  onFileSelect: () => void
  onImageSelect: () => void
  onLibrarySelect: () => void
  libraryFileCount: number
  panelLabel?: string
  fixedContextMode?: '1m' | '200k'
  hasPendingContent: boolean
  textareaRef: React.RefObject<HTMLTextAreaElement | null>
  /** Optional initial value (used for draft restore) */
  initialValue?: string
  /** Called on every keystroke for draft saving */
  onDraftChange?: (text: string) => void
}

export const WorkspaceChatInput = React.memo(
  React.forwardRef<WorkspaceChatInputHandle, WorkspaceChatInputProps>(function WorkspaceChatInput({
  onSend,
  onKeyDown,
  onPaste,
  placeholder,
  disabled,
  isWalkieTalkieMode,
  isLoading,
  firstMessageSent,
  onEndSession,
  onCancelSession,
  onFileSelect,
  onImageSelect,
  onLibrarySelect,
  libraryFileCount,
  panelLabel,
  fixedContextMode,
  hasPendingContent,
  textareaRef,
  initialValue,
  onDraftChange,
}, ref) {
  // INPUT STATE LIVES HERE — not in parent. Parent re-renders do NOT trigger re-renders here.
  const [inputValue, setInputValue] = useState(initialValue ?? '')

  // Expose getValue/setValue/clear to parent via ref
  useImperativeHandle(ref, () => ({
    getValue: () => inputValue,
    setValue: (v: string) => setInputValue(v),
    clear: () => setInputValue(''),
  }), [inputValue])

  // Restore initial value when it changes (conversation switch)
  useEffect(() => {
    if (initialValue !== undefined) setInputValue(initialValue)
  }, [initialValue])

  // Notify parent of draft changes (debounced in parent)
  useEffect(() => {
    onDraftChange?.(inputValue)
  }, [inputValue, onDraftChange])

  const handleLocalSend = useCallback(() => {
    const text = inputValue.trim()
    if (!text && !hasPendingContent) return
    onSend(text)
    setInputValue('')
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [inputValue, hasPendingContent, onSend, textareaRef])

  const handleLocalKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleLocalSend()
      return
    }
    onKeyDown?.(e)
  }, [handleLocalSend, onKeyDown])
  return (
    <>
      <div className="flex gap-2">
        {/* File upload button */}
        <Button
          variant="ghost"
          size="sm"
          className="h-[44px] px-2 text-muted-foreground hover:text-foreground"
          onClick={onFileSelect}
          disabled={isLoading || disabled}
          title="Attach file"
        >
          <Paperclip size={18} />
        </Button>

        {/* Image upload button */}
        <Button
          variant="ghost"
          size="sm"
          className="h-[44px] px-2 text-muted-foreground hover:text-foreground"
          onClick={onImageSelect}
          disabled={isLoading || disabled}
          title="Attach image"
        >
          <ImagePlus size={18} />
        </Button>

        {/* Attach from Library button */}
        <Button
          variant="ghost"
          size="sm"
          className={`h-[44px] px-2 ${libraryFileCount > 0 ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
          onClick={onLibrarySelect}
          disabled={isLoading || disabled}
          title={libraryFileCount > 0 ? `${libraryFileCount} library file(s) attached` : 'Attach from Library'}
        >
          <BookOpen size={18} />
          {libraryFileCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
              {libraryFileCount}
            </span>
          )}
        </Button>

        <textarea
          ref={textareaRef as React.RefObject<HTMLTextAreaElement>}
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value)
            // Auto-expand: reset height then set to scrollHeight (capped by max-h)
            const el = e.target
            el.style.height = 'auto'
            el.style.height = `${Math.min(el.scrollHeight, 240)}px`
          }}
          onKeyDown={handleLocalKeyDown}
          onPaste={onPaste}
          placeholder={placeholder}
          disabled={disabled}
          className={`flex-1 resize-y min-h-[44px] max-h-[240px] rounded-md border px-3 py-2 text-sm outline-none focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50 ${
            isWalkieTalkieMode
              ? 'border-emerald-500 ring-emerald-500/30 bg-emerald-500/5 text-foreground placeholder:text-emerald-400/60'
              : 'border-border bg-input text-foreground placeholder:text-muted-foreground ring-ring'
          }`}
          rows={1}
        />
        {isLoading ? (
          <div className="flex gap-1">
            {firstMessageSent && (
              <Button
                onClick={handleLocalSend}
                disabled={!inputValue.trim()}
                title="Send via walkie-talkie (no extra API cost)"
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <Send size={16} />
              </Button>
            )}
            <Button
              onClick={onEndSession}
              title="End session gracefully (writes handoff)"
              className="bg-orange-600 hover:bg-orange-700 text-white"
            >
              <LogOut size={16} />
            </Button>
            <Button
              onClick={onCancelSession}
              title="Force stop agent"
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              <Square size={16} className="fill-current" />
            </Button>
          </div>
        ) : (
          <Button
            onClick={handleLocalSend}
            disabled={(!inputValue.trim() && !hasPendingContent) || disabled}
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
        {isWalkieTalkieMode
          ? 'Walkie-talkie mode — messages sent without extra API cost. Enter to send.'
          : 'Enter to send, Shift+Enter for new line. Drag & drop or paste images.'}
      </p>
    </>
  )
}))
