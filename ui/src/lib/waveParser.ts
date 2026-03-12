/**
 * waveParser — Parse parallel wave declarations from LLM phase-split output.
 *
 * The phase-splitting prompt instructs the LLM to output execution waves like:
 *   "Wave 1: [Phase 1] → Wave 2: [Phase 2, Phase 3] (parallel) → Wave 3: [Phase 4]"
 *
 * This module parses that format into a numeric array-of-arrays:
 *   [[1], [2, 3], [4]]
 *
 * Falls back to sequential [[1], [2], ..., [N]] if parsing fails.
 */

/**
 * Parse "Wave X: [Phase N, Phase M]" lines from LLM output.
 * Returns array of waves, each wave is an array of phase numbers.
 *
 * @example
 * parseWaves("Wave 1: [Phase 1] → Wave 2: [Phase 2, Phase 3]")
 * // → [[1], [2, 3]]
 */
export function parseWaves(phaseOutput: string): number[][] {
  const waves: number[][] = []
  // Match "Wave N: [...]" patterns (case-insensitive, various separators)
  const waveRegex = /Wave\s+(\d+)\s*:?\s*\[([^\]]+)\]/gi
  let match: RegExpExecArray | null

  while ((match = waveRegex.exec(phaseOutput)) !== null) {
    const phaseList = match[2]
    const phaseNums = phaseList
      .split(/,\s*/)
      .map(s => {
        // Extract number from strings like "Phase 2", "2", "phase2"
        const numMatch = s.match(/\d+/)
        return numMatch ? parseInt(numMatch[0], 10) : NaN
      })
      .filter(n => !isNaN(n) && n > 0)

    if (phaseNums.length > 0) {
      waves.push(phaseNums)
    }
  }

  return waves
}

/**
 * Get wave index (0-based) for a given phase number.
 * Returns -1 if not found in any wave.
 */
export function getWaveForPhase(waves: number[][], phaseNum: number): number {
  return waves.findIndex(wave => wave.includes(phaseNum))
}

/**
 * Check if a phase runs in parallel with any other phase (same wave, wave size > 1).
 */
export function isParallelPhase(waves: number[][], phaseNum: number): boolean {
  const waveIdx = getWaveForPhase(waves, phaseNum)
  if (waveIdx === -1) return false
  return waves[waveIdx].length > 1
}

/**
 * Build a sequential fallback: each phase is its own wave.
 */
export function sequentialWaves(numPhases: number): number[][] {
  return Array.from({ length: numPhases }, (_, i) => [i + 1])
}
