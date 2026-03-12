/**
 * ClearButton - Small X icon for clearing text fields.
 *
 * Positioned at the right edge of input/textarea containers.
 * Shows a confirmation dialog if the content exceeds 100 characters
 * to prevent accidental data loss.
 */

import { X } from 'lucide-react'
import { useCallback, useState } from 'react'

interface ClearButtonProps {
  /** Current field value — used to decide whether to show confirmation */
  value: string
  /** Called when the user confirms they want to clear */
  onClear: () => void
  /** Additional CSS classes for positioning */
  className?: string
}

export function ClearButton({ value, onClear, className = '' }: ClearButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false)

  const handleClick = useCallback(() => {
    // No content — nothing to clear
    if (!value) return

    // Short content — clear immediately without confirmation
    if (value.length <= 100) {
      onClear()
      return
    }

    // Long content — ask for confirmation
    setShowConfirm(true)
  }, [value, onClear])

  const handleConfirm = useCallback(() => {
    onClear()
    setShowConfirm(false)
  }, [onClear])

  const handleCancel = useCallback(() => {
    setShowConfirm(false)
  }, [])

  // Only show when there is content to clear
  if (!value) return null

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        className={`text-zinc-500 hover:text-orange-400 transition-colors p-0.5 rounded ${className}`}
        title="Clear field"
      >
        <X size={14} />
      </button>

      {/* Confirmation overlay for long content */}
      {showConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-5 max-w-sm shadow-2xl space-y-3">
            <p className="text-sm text-white font-medium">Clear this field?</p>
            <p className="text-xs text-zinc-400">
              This field has {value.length.toLocaleString()} characters. This action cannot be undone.
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={handleCancel}
                className="px-3 py-1.5 text-xs text-zinc-400 hover:text-white border border-zinc-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                className="px-3 py-1.5 text-xs text-white bg-orange-600 hover:bg-orange-500 rounded-lg transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
