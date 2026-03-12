/**
 * Combiner - Three output slots that merge checked rule blocks.
 *
 * Slots: Main Combined, Phase 1 Combo, Phase 2+ Combo.
 * Each slot shows a checkbox list of all rule blocks. Checking/unchecking
 * is two-way bound with the RuleBlock sidebar checkboxes (Main, P1, P2+).
 * Preview shows merged text and estimated token count.
 */

import { useCallback } from 'react'
import { RefreshCw } from 'lucide-react'
import type { RuleBlockData } from './RuleBlock'

// Rough token estimation: 1 token ~ 4 chars
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)
}

// ---------------------------------------------------------------------------
// Single combiner slot
// ---------------------------------------------------------------------------

type SlotKey = 'combiner_main' | 'combiner_p1' | 'combiner_p2plus'

interface CombinerSlotProps {
  title: string
  slotKey: SlotKey
  blocks: RuleBlockData[]
  onToggleBlock: (blockId: string, slotKey: SlotKey, checked: boolean) => void
  /** Color class for the accent (border, title) */
  accentClass: string
}

function CombinerSlot({ title, slotKey, blocks, onToggleBlock, accentClass }: CombinerSlotProps) {
  // Merge checked blocks in order
  const checkedBlocks = blocks
    .filter((b) => b[slotKey] && b.content.trim())
    .sort((a, b) => a.order - b.order)

  const mergedText = checkedBlocks.map((b) => b.content.trim()).join('\n\n')
  const tokenCount = estimateTokens(mergedText)

  return (
    <div className={`border rounded-lg overflow-hidden ${accentClass}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-zinc-800/30">
        <span className="text-xs font-medium text-zinc-300">{title}</span>
        <span className="text-[10px] text-zinc-500">{tokenCount.toLocaleString()} tokens</span>
      </div>

      {/* Checkbox list */}
      <div className="px-3 py-2 space-y-1 border-t border-zinc-800/50">
        {blocks.map((block) => (
          <label
            key={block.id}
            className="flex items-center gap-2 cursor-pointer text-xs py-0.5"
          >
            <input
              type="checkbox"
              checked={block[slotKey]}
              onChange={(e) => onToggleBlock(block.id, slotKey, e.target.checked)}
              className="w-3 h-3 rounded border-zinc-600 bg-zinc-900 text-orange-500"
            />
            <span className={block[slotKey] ? 'text-zinc-300' : 'text-zinc-600'}>
              {block.name || 'Untitled block'}
            </span>
          </label>
        ))}
        {blocks.length === 0 && (
          <p className="text-[10px] text-zinc-600 py-1">No rule blocks created yet</p>
        )}
      </div>

      {/* Preview */}
      {mergedText && (
        <div className="px-3 py-2 border-t border-zinc-800/50">
          <p className="text-[10px] text-zinc-600 mb-1">Preview:</p>
          <div className="text-[10px] text-zinc-500 max-h-16 overflow-y-auto whitespace-pre-wrap leading-relaxed">
            {mergedText.length > 200
              ? mergedText.slice(0, 200) + '...'
              : mergedText}
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Combiner — three slots
// ---------------------------------------------------------------------------

interface CombinerProps {
  blocks: RuleBlockData[]
  onBlocksChange: (blocks: RuleBlockData[]) => void
}

export function Combiner({ blocks, onBlocksChange }: CombinerProps) {
  const handleToggleBlock = useCallback(
    (blockId: string, slotKey: SlotKey, checked: boolean) => {
      onBlocksChange(
        blocks.map((b) =>
          b.id === blockId ? { ...b, [slotKey]: checked } : b
        )
      )
    },
    [blocks, onBlocksChange]
  )

  // Re-pull doesn't change data — it's just for UI feedback.
  // In this implementation, the merge is always live (computed from checked blocks).
  // The re-pull button exists for when users edit block content and want to
  // "see" the refresh happen, but since we compute on render, it's a no-op.

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-medium text-zinc-300">Combiner Slots</h3>
        <button
          onClick={() => {
            // Force a re-render by touching updated_at on all blocks
            onBlocksChange(
              blocks.map((b) => ({ ...b, updated_at: new Date().toISOString() }))
            )
          }}
          className="flex items-center gap-1 text-[10px] text-zinc-500 hover:text-orange-400 transition-colors px-1.5 py-0.5 rounded border border-zinc-700/50 hover:border-orange-500/30"
          title="Re-merge from checked blocks"
        >
          <RefreshCw size={10} />
          Re-pull
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <CombinerSlot
          title="Main Combined"
          slotKey="combiner_main"
          blocks={blocks}
          onToggleBlock={handleToggleBlock}
          accentClass="border-zinc-700/60"
        />
        <CombinerSlot
          title="Phase 1 Combo"
          slotKey="combiner_p1"
          blocks={blocks}
          onToggleBlock={handleToggleBlock}
          accentClass="border-orange-700/40"
        />
        <CombinerSlot
          title="Phase 2+ Combo"
          slotKey="combiner_p2plus"
          blocks={blocks}
          onToggleBlock={handleToggleBlock}
          accentClass="border-cyan-700/40"
        />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Helper: get merged text for a specific slot
// ---------------------------------------------------------------------------

export function getMergedText(blocks: RuleBlockData[], slot: 'main' | 'p1' | 'p2plus'): string {
  const slotKey: SlotKey =
    slot === 'main' ? 'combiner_main' :
    slot === 'p1' ? 'combiner_p1' :
    'combiner_p2plus'

  return blocks
    .filter((b) => b[slotKey] && b.content.trim())
    .sort((a, b) => a.order - b.order)
    .map((b) => b.content.trim())
    .join('\n\n')
}
