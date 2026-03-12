/**
 * RuleBlock - Named, persistent rule block for the Build Rules Library.
 *
 * Each block has:
 * - Name (editable header)
 * - Content (lockable textarea)
 * - Three combiner checkboxes (Main, P1, P2+)
 * - Tags (filterable metadata)
 * - Edit/Lock toggle, Clear, Delete
 */

import { useState, useCallback } from 'react'
import {
  Lock,
  Unlock,
  Trash2,
  X,
  Plus,
  GripVertical,
} from 'lucide-react'
import { ClearButton } from './ClearButton'

// ---------------------------------------------------------------------------
// Types — shared between RuleBlock, Combiner, and persistence
// ---------------------------------------------------------------------------

export interface RuleBlockData {
  id: string
  name: string
  content: string
  tags: string[]
  label: string
  order: number
  combiner_main: boolean
  combiner_p1: boolean
  combiner_p2plus: boolean
  created_at: string
  updated_at: string
}

export function createEmptyBlock(order: number): RuleBlockData {
  const now = new Date().toISOString()
  return {
    id: crypto.randomUUID(),
    name: '',
    content: '',
    tags: [],
    label: '',
    order,
    combiner_main: false,
    combiner_p1: false,
    combiner_p2plus: false,
    created_at: now,
    updated_at: now,
  }
}

// ---------------------------------------------------------------------------
// RuleBlockCard
// ---------------------------------------------------------------------------

interface RuleBlockCardProps {
  block: RuleBlockData
  onUpdate: (id: string, updates: Partial<RuleBlockData>) => void
  onDelete: (id: string) => void
}

export function RuleBlockCard({ block, onUpdate, onDelete }: RuleBlockCardProps) {
  const [editing, setEditing] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [tagInput, setTagInput] = useState('')

  const handleToggleEdit = useCallback(() => {
    if (editing) {
      // Locking — update timestamp
      onUpdate(block.id, { updated_at: new Date().toISOString() })
    }
    setEditing(!editing)
  }, [editing, block.id, onUpdate])

  const handleAddTag = useCallback(() => {
    const tag = tagInput.trim().toLowerCase()
    if (tag && !block.tags.includes(tag)) {
      onUpdate(block.id, { tags: [...block.tags, tag] })
    }
    setTagInput('')
  }, [tagInput, block.id, block.tags, onUpdate])

  const handleRemoveTag = useCallback((tag: string) => {
    onUpdate(block.id, { tags: block.tags.filter(t => t !== tag) })
  }, [block.id, block.tags, onUpdate])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAddTag()
    }
  }, [handleAddTag])

  return (
    <div className="bg-zinc-800/40 border border-zinc-700/60 rounded-lg overflow-hidden group">
      {/* Header row */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-zinc-700/40">
        {/* Drag handle */}
        <GripVertical size={14} className="text-zinc-600 cursor-grab shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />

        {/* Block name */}
        <input
          type="text"
          value={block.name}
          onChange={(e) => onUpdate(block.id, { name: e.target.value })}
          readOnly={!editing}
          placeholder="Rule block name..."
          className={`flex-1 bg-transparent text-sm font-medium text-white placeholder-zinc-600 outline-none min-w-0 ${!editing ? 'cursor-default' : ''}`}
        />

        {/* Combiner checkboxes — right rail */}
        <div className="flex items-center gap-2 shrink-0">
          <label className="flex items-center gap-1 cursor-pointer" title="Include in Main Combined">
            <input
              type="checkbox"
              checked={block.combiner_main}
              onChange={(e) => onUpdate(block.id, { combiner_main: e.target.checked })}
              className="w-3 h-3 rounded border-zinc-600 bg-zinc-900 text-orange-500"
            />
            <span className="text-[10px] text-zinc-500">Main</span>
          </label>
          <label className="flex items-center gap-1 cursor-pointer" title="Include in Phase 1 Combo">
            <input
              type="checkbox"
              checked={block.combiner_p1}
              onChange={(e) => onUpdate(block.id, { combiner_p1: e.target.checked })}
              className="w-3 h-3 rounded border-zinc-600 bg-zinc-900 text-orange-500"
            />
            <span className="text-[10px] text-orange-400">P1</span>
          </label>
          <label className="flex items-center gap-1 cursor-pointer" title="Include in Phase 2+ Combo">
            <input
              type="checkbox"
              checked={block.combiner_p2plus}
              onChange={(e) => onUpdate(block.id, { combiner_p2plus: e.target.checked })}
              className="w-3 h-3 rounded border-zinc-600 bg-zinc-900 text-cyan-500"
            />
            <span className="text-[10px] text-cyan-400">P2+</span>
          </label>
        </div>

        {/* Edit/Lock toggle */}
        <button
          onClick={handleToggleEdit}
          className={`p-1 rounded transition-colors ${
            editing ? 'text-orange-400 hover:text-orange-300' : 'text-zinc-500 hover:text-zinc-300'
          }`}
          title={editing ? 'Lock' : 'Edit'}
        >
          {editing ? <Unlock size={14} /> : <Lock size={14} />}
        </button>

        {/* Clear content */}
        <ClearButton
          value={block.content}
          onClear={() => onUpdate(block.id, { content: '' })}
        />

        {/* Delete */}
        <button
          onClick={() => setShowDeleteConfirm(true)}
          className="text-zinc-600 hover:text-red-400 transition-colors p-1"
          title="Delete block"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {/* Content area */}
      <div className="px-3 py-2">
        {editing ? (
          <textarea
            value={block.content}
            onChange={(e) => onUpdate(block.id, { content: e.target.value })}
            rows={4}
            placeholder="Enter your rules here..."
            className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors resize-y"
          />
        ) : (
          <div className="text-sm text-zinc-400 whitespace-pre-wrap max-h-24 overflow-y-auto leading-relaxed">
            {block.content || (
              <span className="text-zinc-600 italic">No content — click Edit to add rules</span>
            )}
          </div>
        )}
      </div>

      {/* Tags row */}
      <div className="px-3 pb-2 flex items-center gap-1.5 flex-wrap">
        {block.tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-0.5 text-[10px] bg-zinc-700/50 text-zinc-400 px-1.5 py-0.5 rounded-full"
          >
            {tag}
            <button
              onClick={() => handleRemoveTag(tag)}
              className="text-zinc-500 hover:text-red-400 transition-colors"
            >
              <X size={8} />
            </button>
          </span>
        ))}
        <div className="inline-flex items-center gap-0.5">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="+ tag"
            className="bg-transparent text-[10px] text-zinc-500 placeholder-zinc-700 outline-none w-12"
          />
          {tagInput.trim() && (
            <button
              onClick={handleAddTag}
              className="text-zinc-500 hover:text-orange-400 transition-colors"
            >
              <Plus size={10} />
            </button>
          )}
        </div>
      </div>

      {/* Delete confirmation overlay */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-5 max-w-sm shadow-2xl space-y-3">
            <p className="text-sm text-white font-medium">Delete "{block.name || 'Untitled block'}"?</p>
            <p className="text-xs text-zinc-400">
              This will remove the block and all its content. This cannot be undone.
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-3 py-1.5 text-xs text-zinc-400 hover:text-white border border-zinc-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onDelete(block.id)
                  setShowDeleteConfirm(false)
                }}
                className="px-3 py-1.5 text-xs text-white bg-red-600 hover:bg-red-500 rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// RuleBlockLibrary — Container with tag filter and add button
// ---------------------------------------------------------------------------

interface RuleBlockLibraryProps {
  blocks: RuleBlockData[]
  onBlocksChange: (blocks: RuleBlockData[]) => void
}

export function RuleBlockLibrary({ blocks, onBlocksChange }: RuleBlockLibraryProps) {
  const [activeTag, setActiveTag] = useState<string | null>(null)

  // All unique tags across all blocks
  const allTags = Array.from(new Set(blocks.flatMap((b) => b.tags))).sort()

  // Filtered blocks (by tag if active)
  const displayBlocks = activeTag
    ? blocks.filter((b) => b.tags.includes(activeTag))
    : blocks

  const handleUpdate = useCallback(
    (id: string, updates: Partial<RuleBlockData>) => {
      onBlocksChange(
        blocks.map((b) => (b.id === id ? { ...b, ...updates } : b))
      )
    },
    [blocks, onBlocksChange]
  )

  const handleDelete = useCallback(
    (id: string) => {
      onBlocksChange(blocks.filter((b) => b.id !== id))
    },
    [blocks, onBlocksChange]
  )

  const handleAddBlock = useCallback(() => {
    const maxOrder = blocks.length > 0 ? Math.max(...blocks.map((b) => b.order)) : -1
    const newBlock = createEmptyBlock(maxOrder + 1)
    onBlocksChange([...blocks, newBlock])
  }, [blocks, onBlocksChange])

  return (
    <div className="space-y-3">
      {/* Tag filter bar */}
      {allTags.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] text-zinc-600 mr-1">Filter:</span>
          {allTags.map((tag) => (
            <button
              key={tag}
              onClick={() => setActiveTag(activeTag === tag ? null : tag)}
              className={`text-[10px] px-2 py-0.5 rounded-full border transition-colors ${
                activeTag === tag
                  ? 'bg-orange-500/20 border-orange-500/40 text-orange-400'
                  : 'bg-zinc-800/50 border-zinc-700/50 text-zinc-500 hover:text-zinc-300 hover:border-zinc-600'
              }`}
            >
              {tag}
            </button>
          ))}
          {activeTag && (
            <button
              onClick={() => setActiveTag(null)}
              className="text-[10px] text-zinc-600 hover:text-zinc-400 transition-colors"
            >
              Clear filter
            </button>
          )}
        </div>
      )}

      {/* Block list */}
      <div className="space-y-2 max-h-[600px] overflow-y-auto">
        {displayBlocks.length === 0 ? (
          <div className="text-center py-6 text-zinc-600 text-sm">
            {activeTag
              ? `No blocks tagged "${activeTag}"`
              : 'No rule blocks yet. Click "+ New Block" to create one.'}
          </div>
        ) : (
          displayBlocks.map((block) => (
            <RuleBlockCard
              key={block.id}
              block={block}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>

      {/* Add button */}
      <button
        onClick={handleAddBlock}
        className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-orange-400 transition-colors px-3 py-2 rounded-lg border border-dashed border-zinc-700 hover:border-orange-500/50 w-full justify-center"
      >
        <Plus size={14} />
        New Block
      </button>
    </div>
  )
}
