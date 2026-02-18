/**
 * useWorkspaceKeyboardShortcuts - Custom hook for workspace-specific keyboard shortcuts.
 *
 * Follows the same pattern as keyboard shortcuts in App.tsx but with
 * workspace-specific bindings: Ctrl+N (new conversation), Ctrl+B (toggle
 * sidebar), Ctrl+L (toggle library), Ctrl+F (focus search), Ctrl+E (export),
 * / (focus chat input), ? (show help).
 */

import { useEffect } from 'react'

interface UseWorkspaceKeyboardShortcutsOptions {
  onNewConversation: () => void
  onToggleLibrary: () => void
  onToggleSidebar: () => void
  onFocusSearch: () => void
  onExportChat: () => void
  onShowShortcutsHelp: () => void
  onFocusChatInput: () => void
  hasActiveConversation: boolean
  /** Toggle panel 1 (Research) — only active in split view */
  onTogglePanel1?: () => void
  /** Toggle panel 2 (PRD Builder) — only active in split view */
  onTogglePanel2?: () => void
  /** Toggle panel 3 (Coder) — only active in split view */
  onTogglePanel3?: () => void
}

/** Registers workspace keyboard shortcut listeners. */
export function useWorkspaceKeyboardShortcuts(
  options: UseWorkspaceKeyboardShortcutsOptions,
): void {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input or textarea (except Escape)
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        if (e.key !== 'Escape') return
      }

      const isMod = e.metaKey || e.ctrlKey

      // Ctrl/Cmd+N: New conversation
      if (isMod && e.key === 'n') {
        e.preventDefault()
        options.onNewConversation()
        return
      }

      // Ctrl/Cmd+L: Toggle library panel
      if (isMod && e.key === 'l') {
        e.preventDefault()
        options.onToggleLibrary()
        return
      }

      // Ctrl/Cmd+B: Toggle sidebar
      if (isMod && e.key === 'b') {
        e.preventDefault()
        options.onToggleSidebar()
        return
      }

      // Ctrl/Cmd+F: Focus search in sidebar
      if (isMod && e.key === 'f') {
        e.preventDefault()
        options.onFocusSearch()
        return
      }

      // Ctrl/Cmd+E: Export current chat
      if (isMod && e.key === 'e' && options.hasActiveConversation) {
        e.preventDefault()
        options.onExportChat()
        return
      }

      // / : Focus chat input (only when not already in an input)
      if (
        e.key === '/' &&
        !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)
      ) {
        e.preventDefault()
        options.onFocusChatInput()
        return
      }

      // 1, 2, 3: Toggle split-view panels
      if (e.key === '1' && options.onTogglePanel1) {
        e.preventDefault()
        options.onTogglePanel1()
        return
      }
      if (e.key === '2' && options.onTogglePanel2) {
        e.preventDefault()
        options.onTogglePanel2()
        return
      }
      if (e.key === '3' && options.onTogglePanel3) {
        e.preventDefault()
        options.onTogglePanel3()
        return
      }

      // ? : Show keyboard shortcuts help
      if (
        e.key === '?' &&
        !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)
      ) {
        e.preventDefault()
        options.onShowShortcutsHelp()
        return
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [options])
}
