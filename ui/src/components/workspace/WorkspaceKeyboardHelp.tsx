/**
 * WorkspaceKeyboardHelp - Keyboard shortcuts help modal for the workspace.
 *
 * Follows the same pattern as KeyboardShortcutsHelp.tsx in the main app.
 * Displays Cmd on macOS, Ctrl on other platforms.
 */

import { useEffect, useCallback } from 'react'
import { Keyboard } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'

interface Shortcut {
  key: string
  description: string
  context?: string
}

const isMac = typeof navigator !== 'undefined' && navigator.platform.includes('Mac')
const modKey = isMac ? 'Cmd' : 'Ctrl'

const shortcuts: Shortcut[] = [
  { key: `${modKey}+N`, description: 'New conversation' },
  { key: `${modKey}+L`, description: 'Toggle library panel' },
  { key: `${modKey}+B`, description: 'Toggle sidebar' },
  { key: `${modKey}+F`, description: 'Focus search' },
  { key: `${modKey}+E`, description: 'Export current chat', context: 'with active chat' },
  { key: '/', description: 'Focus chat input' },
  { key: '1', description: 'Toggle Research panel', context: 'split view' },
  { key: '2', description: 'Toggle PRD Builder panel', context: 'split view' },
  { key: '3', description: 'Toggle Coder panel', context: 'split view' },
  { key: '?', description: 'Show this help' },
  { key: 'Esc', description: 'Close modal' },
]

interface WorkspaceKeyboardHelpProps {
  isOpen: boolean
  onClose: () => void
}

/** Keyboard shortcuts help dialog for the workspace. */
export function WorkspaceKeyboardHelp({
  isOpen,
  onClose,
}: WorkspaceKeyboardHelpProps): React.JSX.Element {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === '?') {
        e.preventDefault()
        onClose()
      }
    },
    [onClose],
  )

  useEffect(() => {
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown)
      return () => window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, handleKeyDown])

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard size={20} className="text-primary" />
            Workspace Shortcuts
          </DialogTitle>
        </DialogHeader>

        <ul className="space-y-1">
          {shortcuts.map((shortcut) => (
            <li
              key={shortcut.key}
              className="flex items-center justify-between py-2 border-b border-border/50 last:border-0"
            >
              <div className="flex items-center gap-3">
                <kbd className="px-2 py-1 text-xs font-mono bg-muted rounded border border-border min-w-[2rem] text-center">
                  {shortcut.key}
                </kbd>
                <span className="text-sm">{shortcut.description}</span>
              </div>
              {shortcut.context && (
                <Badge variant="secondary" className="text-xs">
                  {shortcut.context}
                </Badge>
              )}
            </li>
          ))}
        </ul>

        <p className="text-xs text-muted-foreground text-center pt-2">
          Press ? or Esc to close
        </p>
      </DialogContent>
    </Dialog>
  )
}
