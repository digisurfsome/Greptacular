/**
 * CategoryManager
 *
 * Modal dialog for managing workspace categories. Supports creating,
 * editing, deleting, and reordering categories with preset color
 * selection and up/down arrow reordering.
 */

import { useState, useCallback, useEffect } from 'react'
import { X, Plus, Trash2, Pencil, Check, ChevronUp, ChevronDown } from 'lucide-react'
import type { WorkspaceCategory } from '@/lib/types'

const PRESET_COLORS = [
  '#3b82f6',
  '#22c55e',
  '#eab308',
  '#f97316',
  '#ef4444',
  '#a855f7',
  '#ec4899',
  '#06b6d4',
  '#6366f1',
  '#84cc16',
] as const

interface CategoryManagerProps {
  open: boolean
  onClose: () => void
  categories: WorkspaceCategory[]
  onCreateCategory: (name: string, color: string) => Promise<void>
  onUpdateCategory: (id: number, name: string, color: string) => Promise<void>
  onDeleteCategory: (id: number) => Promise<void>
  onReorderCategories: (orderedIds: number[]) => Promise<void>
}

/** Modal for managing workspace categories with CRUD and reordering. */
export function CategoryManager({
  open,
  onClose,
  categories,
  onCreateCategory,
  onUpdateCategory,
  onDeleteCategory,
  onReorderCategories,
}: CategoryManagerProps): React.JSX.Element | null {
  const [newName, setNewName] = useState('')
  const [newColor, setNewColor] = useState<string>(PRESET_COLORS[0])
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editColor, setEditColor] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  // Close on Escape key
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  const handleCreate = useCallback(async () => {
    const trimmed = newName.trim()
    if (!trimmed) return
    setIsCreating(true)
    try {
      await onCreateCategory(trimmed, newColor)
      setNewName('')
      setNewColor(PRESET_COLORS[0])
    } finally {
      setIsCreating(false)
    }
  }, [newName, newColor, onCreateCategory])

  const handleStartEdit = useCallback((cat: WorkspaceCategory) => {
    setEditingId(cat.id)
    setEditName(cat.name)
    setEditColor(cat.color || PRESET_COLORS[0])
  }, [])

  const handleSaveEdit = useCallback(async () => {
    if (editingId === null) return
    const trimmed = editName.trim()
    if (!trimmed) return
    await onUpdateCategory(editingId, trimmed, editColor)
    setEditingId(null)
  }, [editingId, editName, editColor, onUpdateCategory])

  const handleMoveUp = useCallback(async (index: number) => {
    if (index === 0) return
    const ids = categories.map(c => c.id)
    ;[ids[index - 1], ids[index]] = [ids[index], ids[index - 1]]
    await onReorderCategories(ids)
  }, [categories, onReorderCategories])

  const handleMoveDown = useCallback(async (index: number) => {
    if (index >= categories.length - 1) return
    const ids = categories.map(c => c.id)
    ;[ids[index], ids[index + 1]] = [ids[index + 1], ids[index]]
    await onReorderCategories(ids)
  }, [categories, onReorderCategories])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        className="bg-card border border-border rounded-lg shadow-lg max-w-md w-full mx-4 max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-foreground">Manage Categories</h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Category list */}
        <div className="flex-1 overflow-y-auto px-4 py-2 space-y-1">
          {categories.length === 0 && (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No categories yet. Create one below.
            </p>
          )}

          {categories.map((cat, index) => (
            <div
              key={cat.id}
              className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-muted/50"
            >
              {editingId === cat.id ? (
                <>
                  <span
                    className="w-4 h-4 rounded-full flex-shrink-0 border border-border"
                    style={{ backgroundColor: editColor }}
                  />
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="flex-1 text-sm bg-input border border-border rounded px-2 py-0.5 text-foreground outline-none ring-ring focus:ring-1"
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSaveEdit() }}
                    autoFocus
                  />
                  <div className="flex gap-0.5">
                    {PRESET_COLORS.map(c => (
                      <button
                        key={c}
                        onClick={() => setEditColor(c)}
                        className={`w-4 h-4 rounded-full border-2 ${editColor === c ? 'border-primary' : 'border-transparent'}`}
                        style={{ backgroundColor: c }}
                      />
                    ))}
                  </div>
                  <button
                    onClick={handleSaveEdit}
                    className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
                  >
                    <Check size={14} />
                  </button>
                </>
              ) : (
                <>
                  <span
                    className="w-4 h-4 rounded-full flex-shrink-0 border border-border"
                    style={{ backgroundColor: cat.color || '#888' }}
                  />
                  <span className="flex-1 text-sm text-foreground truncate">{cat.name}</span>
                  <button
                    onClick={() => handleMoveUp(index)}
                    disabled={index === 0}
                    className="p-0.5 rounded hover:bg-accent text-muted-foreground disabled:opacity-30"
                  >
                    <ChevronUp size={12} />
                  </button>
                  <button
                    onClick={() => handleMoveDown(index)}
                    disabled={index >= categories.length - 1}
                    className="p-0.5 rounded hover:bg-accent text-muted-foreground disabled:opacity-30"
                  >
                    <ChevronDown size={12} />
                  </button>
                  <button
                    onClick={() => handleStartEdit(cat)}
                    className="p-0.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
                  >
                    <Pencil size={12} />
                  </button>
                  <button
                    onClick={() => onDeleteCategory(cat.id)}
                    className="p-0.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 size={12} />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Add category form */}
        <div className="border-t border-border px-4 py-3 space-y-2">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="New category name..."
              className="flex-1 text-sm bg-input border border-border rounded px-2 py-1.5 text-foreground placeholder:text-muted-foreground outline-none ring-ring focus:ring-1"
              onKeyDown={(e) => { if (e.key === 'Enter') handleCreate() }}
            />
            <button
              onClick={handleCreate}
              disabled={!newName.trim() || isCreating}
              className="flex items-center gap-1 px-3 py-1.5 text-sm rounded bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Plus size={14} />
              Add
            </button>
          </div>
          <div className="flex gap-1.5">
            {PRESET_COLORS.map(c => (
              <button
                key={c}
                onClick={() => setNewColor(c)}
                className={`w-6 h-6 rounded-full border-2 ${newColor === c ? 'border-primary ring-2 ring-ring ring-offset-1' : 'border-transparent'}`}
                style={{ backgroundColor: c }}
                title={c}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
