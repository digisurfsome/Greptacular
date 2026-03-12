/**
 * PromptBar — Collapsible prompt editor with lock/edit toggle.
 *
 * Default state: locked + collapsed (slim bar showing just the label).
 * Edit button: unlocks and expands to show a full editable textarea.
 * Lock button: locks back to read-only collapsed state.
 * Reset: restores original default prompt (with confirmation).
 * Token count badge shows estimated tokens for the current value.
 */

import { useState } from 'react'
import { Lock, Unlock, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react'

// ---------------------------------------------------------------------------
// Token estimation helper (1 token ≈ 4 chars)
// ---------------------------------------------------------------------------

function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)
}

// ---------------------------------------------------------------------------
// PromptBar
// ---------------------------------------------------------------------------

export interface PromptBarProps {
  /** Display name shown in the bar header */
  label: string
  /** Current prompt text (controlled) */
  value: string
  /** Original default value for the "Reset to default" action */
  defaultValue: string
  /** Called when the user edits the text */
  onChange: (value: string) => void
  /** Optional icon displayed before the label */
  icon?: React.ReactNode
  /** Override placeholder text */
  placeholder?: string
}

export function PromptBar({
  label,
  value,
  defaultValue,
  onChange,
  icon,
  placeholder,
}: PromptBarProps) {
  const [editing, setEditing] = useState(false)
  const [confirmReset, setConfirmReset] = useState(false)

  const tokenCount = estimateTokens(value ?? defaultValue)
  const isModified = value !== defaultValue

  const handleLock = () => {
    setEditing(false)
  }

  const handleEdit = () => {
    setEditing(true)
  }

  const handleResetClick = () => {
    if (!confirmReset) {
      setConfirmReset(true)
      return
    }
    onChange(defaultValue)
    setConfirmReset(false)
  }

  const handleResetCancel = () => {
    setConfirmReset(false)
  }

  return (
    <div
      className={`border rounded-lg overflow-hidden transition-colors ${
        editing
          ? 'border-orange-500/60 bg-zinc-900/60'
          : 'border-zinc-700/50 bg-zinc-900/20'
      }`}
    >
      {/* Header bar */}
      <div className="flex items-center gap-2 px-3 py-2">
        {/* Icon + label */}
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          {icon && <span className="shrink-0">{icon}</span>}
          <span className="text-xs font-medium text-zinc-300 truncate">{label}</span>
          {isModified && (
            <span className="text-xs text-orange-400 shrink-0">✎ edited</span>
          )}
        </div>

        {/* Token count */}
        <span className="text-xs text-zinc-600 shrink-0">
          {tokenCount.toLocaleString()} tokens
        </span>

        {/* Lock/Edit toggle */}
        {editing ? (
          <button
            onClick={handleLock}
            className="flex items-center gap-1 text-xs text-orange-400 hover:text-orange-300 transition-colors shrink-0 border border-orange-700/40 rounded px-2 py-0.5"
            title="Lock prompt"
          >
            <Lock size={11} />
            Lock
          </button>
        ) : (
          <button
            onClick={handleEdit}
            className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors shrink-0 border border-zinc-700 rounded px-2 py-0.5 hover:border-zinc-500"
            title="Edit prompt"
          >
            <Unlock size={11} />
            Edit
          </button>
        )}

        {/* Collapse/expand indicator when locked */}
        {!editing && (
          <span className="text-zinc-600 shrink-0">
            <ChevronDown size={13} />
          </span>
        )}
        {editing && (
          <span className="text-zinc-600 shrink-0">
            <ChevronUp size={13} />
          </span>
        )}
      </div>

      {/* Expanded textarea */}
      {editing && (
        <div className="px-3 pb-3 pt-0 space-y-2 border-t border-zinc-800">
          <textarea
            value={value ?? defaultValue}
            onChange={e => onChange(e.target.value)}
            rows={8}
            placeholder={placeholder || `${label} prompt...`}
            className="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-zinc-300 text-xs font-mono focus:border-orange-500 focus:outline-none transition-colors resize-y leading-relaxed"
          />
          {/* Reset link */}
          <div className="flex items-center gap-2">
            {!confirmReset ? (
              <button
                onClick={handleResetClick}
                className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <RotateCcw size={10} />
                Reset to default
              </button>
            ) : (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-amber-400">Reset to default? Your changes will be lost.</span>
                <button
                  onClick={handleResetClick}
                  className="text-red-400 hover:text-red-300 transition-colors underline"
                >
                  Confirm
                </button>
                <button
                  onClick={handleResetCancel}
                  className="text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
