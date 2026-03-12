/**
 * GatePopup - Two-choice modal shown before Generate All.
 *
 * Presents two decisions:
 * 1. Build Mode: New Build vs Edit/Patch
 * 2. Phase Mode: Single Phase (Main Combined) vs Split Phase (P1 + P2+ Combos)
 *
 * One click proceeds — the choice IS the confirmation.
 * Last used choices are persisted to localStorage.
 */

import { Layers, Wrench, Hammer } from 'lucide-react'

// ---------------------------------------------------------------------------
// Build mode prefixes — injected before role prompts
// ---------------------------------------------------------------------------

export const NEW_BUILD_PREFIX = `MODE: NEW BUILD
Design the full architecture from scratch. Define file structure, naming conventions, testing framework, DB schema.
Create all files and infrastructure. Follow the architect's plan exactly.
Full documentation: ARCHITECTURE.md, CONVENTIONS.md, SPEC_CURRENT.md.
Test everything end-to-end.`

export const EDIT_PATCH_PREFIX = `MODE: EDIT / PATCH
Study the EXISTING codebase first. Preserve all working code.
Only modify what's needed for the requested changes.
Match existing patterns (imports, naming, indentation).
Do NOT create new pages unless explicitly told to.
Do NOT restructure working code for style.
Focus testing on changed features + regression on adjacent features.
Update existing docs only. Add "Changes Made" section.`

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type BuildMode = 'new' | 'edit'
export type PhaseMode = 'single' | 'split'

interface GatePopupProps {
  /** Whether the popup is visible */
  open: boolean
  /** Called when user makes their choice */
  onConfirm: (buildMode: BuildMode, phaseMode: PhaseMode) => void
  /** Called when user dismisses */
  onCancel: () => void
  /** Token counts for display */
  mainTokens: number
  p1Tokens: number
  p2PlusTokens: number
  /** Last used values (from localStorage) */
  lastBuildMode: BuildMode
  lastPhaseMode: PhaseMode
}

export function GatePopup({
  open,
  onConfirm,
  onCancel,
  mainTokens,
  p1Tokens,
  p2PlusTokens,
  lastBuildMode,
  lastPhaseMode,
}: GatePopupProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70">
      <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl space-y-5">
        {/* Title */}
        <h3 className="text-lg font-semibold text-white text-center">
          What kind of build is this?
        </h3>

        {/* Row 1: Build Mode */}
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => onConfirm('new', lastPhaseMode)}
            className={`flex flex-col items-center gap-2 px-4 py-4 rounded-lg border-2 transition-all hover:bg-zinc-800/50 ${
              lastBuildMode === 'new'
                ? 'border-orange-500/60 bg-orange-500/5'
                : 'border-zinc-700 bg-zinc-800/20'
            }`}
          >
            <Hammer size={24} className="text-orange-400" />
            <span className="text-sm font-semibold text-white">New Build</span>
            <div className="text-[10px] text-zinc-500 text-center space-y-0.5">
              <p>Full architecture</p>
              <p>File structure</p>
              <p>Testing frameworks</p>
              <p>Naming conventions</p>
            </div>
          </button>
          <button
            onClick={() => onConfirm('edit', lastPhaseMode)}
            className={`flex flex-col items-center gap-2 px-4 py-4 rounded-lg border-2 transition-all hover:bg-zinc-800/50 ${
              lastBuildMode === 'edit'
                ? 'border-cyan-500/60 bg-cyan-500/5'
                : 'border-zinc-700 bg-zinc-800/20'
            }`}
          >
            <Wrench size={24} className="text-cyan-400" />
            <span className="text-sm font-semibold text-white">Edit / Patch</span>
            <div className="text-[10px] text-zinc-500 text-center space-y-0.5">
              <p>Respect existing code</p>
              <p>Don't restructure</p>
              <p>Minimal, surgical edits</p>
              <p>Match existing patterns</p>
            </div>
          </button>
        </div>

        {/* Row 2: Phase Mode */}
        <div>
          <p className="text-xs text-zinc-500 mb-2 text-center">How are you splitting phases?</p>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => onConfirm(lastBuildMode, 'single')}
              className={`flex flex-col items-center gap-1.5 px-4 py-3 rounded-lg border-2 transition-all hover:bg-zinc-800/50 ${
                lastPhaseMode === 'single'
                  ? 'border-orange-500/60 bg-orange-500/5'
                  : 'border-zinc-700 bg-zinc-800/20'
              }`}
            >
              <Layers size={18} className="text-zinc-400" />
              <span className="text-xs font-medium text-white">Single Phase</span>
              <span className="text-[10px] text-zinc-500">{mainTokens.toLocaleString()} tokens</span>
            </button>
            <button
              onClick={() => onConfirm(lastBuildMode, 'split')}
              className={`flex flex-col items-center gap-1.5 px-4 py-3 rounded-lg border-2 transition-all hover:bg-zinc-800/50 ${
                lastPhaseMode === 'split'
                  ? 'border-cyan-500/60 bg-cyan-500/5'
                  : 'border-zinc-700 bg-zinc-800/20'
              }`}
            >
              <Layers size={18} className="text-zinc-400" />
              <span className="text-xs font-medium text-white">Split Phase</span>
              <span className="text-[10px] text-zinc-500">
                {p1Tokens.toLocaleString()} + {p2PlusTokens.toLocaleString()} tokens
              </span>
            </button>
          </div>
        </div>

        {/* Last used indicator */}
        <p className="text-[10px] text-zinc-600 text-center">
          Last used: {lastBuildMode === 'new' ? 'New Build' : 'Edit / Patch'} &bull; {lastPhaseMode === 'single' ? 'Single Phase' : 'Split Phase'}
        </p>

        {/* Cancel */}
        <div className="text-center">
          <button
            onClick={onCancel}
            className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
