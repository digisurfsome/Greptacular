/**
 * AgentNotifications
 *
 * Parses structured tags ([SUMMARY], [ROADMAP], [PROGRESS]) from agent
 * messages and renders them as styled, collapsible cards. Each block type
 * gets a distinct color theme and layout:
 *
 * - SUMMARY:  Purple/violet border, FileText icon, plain text body.
 * - ROADMAP:  Amber/yellow border, Map icon, numbered checklist items.
 * - PROGRESS: Cyan/teal border, TrendingUp icon, status-coded lines with
 *             a mini progress bar showing done/total percentage.
 *
 * Also exports `parseStructuredBlocks` for detection and
 * `stripStructuredBlocks` to remove raw tags from the regular renderer.
 */

import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  FileText,
  Map,
  TrendingUp,
  CheckCircle2,
  Loader2,
  Circle,
} from 'lucide-react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface StructuredBlock {
  type: 'summary' | 'roadmap' | 'progress'
  content: string
}

interface AgentNotificationsProps {
  /** Full message content that may contain structured blocks. */
  content: string
  className?: string
}

// ─── Tag Parsing ──────────────────────────────────────────────────────────────

/** Regex patterns for each supported structured tag. */
const BLOCK_PATTERNS: { type: StructuredBlock['type']; regex: RegExp }[] = [
  { type: 'summary', regex: /\[SUMMARY\]([\s\S]*?)\[\/SUMMARY\]/g },
  { type: 'roadmap', regex: /\[ROADMAP\]([\s\S]*?)\[\/ROADMAP\]/g },
  { type: 'progress', regex: /\[PROGRESS\]([\s\S]*?)\[\/PROGRESS\]/g },
]

/**
 * Extract all structured blocks from message content.
 * Returns an array of typed blocks with their inner text, preserving
 * the order in which they appear.
 */
export function parseStructuredBlocks(content: string): StructuredBlock[] {
  const blocks: { type: StructuredBlock['type']; content: string; index: number }[] = []

  for (const { type, regex } of BLOCK_PATTERNS) {
    // Reset lastIndex because we re-use the regex across calls
    const re = new RegExp(regex.source, regex.flags)
    let match: RegExpExecArray | null
    while ((match = re.exec(content)) !== null) {
      blocks.push({ type, content: match[1].trim(), index: match.index })
    }
  }

  // Return blocks sorted by their position in the original content
  blocks.sort((a, b) => a.index - b.index)
  return blocks.map(({ type, content: c }) => ({ type, content: c }))
}

/**
 * Strip all structured block tags from content so the regular message
 * renderer does not show raw tags.
 */
export function stripStructuredBlocks(content: string): string {
  let stripped = content
  for (const { regex } of BLOCK_PATTERNS) {
    stripped = stripped.replace(new RegExp(regex.source, regex.flags), '')
  }
  // Collapse leftover blank lines from removed blocks
  return stripped.replace(/\n{3,}/g, '\n\n').trim()
}

// ─── Sub-components ───────────────────────────────────────────────────────────

/** Collapsible card wrapper shared across block types. */
function BlockCard({
  borderColor,
  icon,
  title,
  defaultExpanded = true,
  children,
}: {
  borderColor: string
  icon: React.ReactNode
  title: string
  defaultExpanded?: boolean
  children: React.ReactNode
}) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  return (
    <div className={`border border-border rounded-md bg-muted/50 overflow-hidden ${borderColor}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 w-full px-3 py-2 text-left text-sm font-medium text-foreground hover:bg-muted/80 transition-colors"
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {icon}
        <span>{title}</span>
      </button>

      {expanded && (
        <div className="border-t border-border px-3 pb-3 pt-2 animate-fade-in">
          {children}
        </div>
      )}
    </div>
  )
}

/** Render a SUMMARY block as readable text. */
function SummaryBlock({ content }: { content: string }) {
  return (
    <BlockCard
      borderColor="border-l-4 border-l-violet-500"
      icon={<FileText size={14} className="text-violet-500" />}
      title="Summary"
    >
      <p className="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed">
        {content}
      </p>
    </BlockCard>
  )
}

/** Render a ROADMAP block as a numbered checklist. */
function RoadmapBlock({ content }: { content: string }) {
  // Split into lines and filter out empties
  const lines = content
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)

  return (
    <BlockCard
      borderColor="border-l-4 border-l-amber-500"
      icon={<Map size={14} className="text-amber-500" />}
      title="Roadmap"
    >
      <ul className="space-y-1.5">
        {lines.map((line, i) => {
          // Strip leading numbering like "1." or "1)" if present
          const cleaned = line.replace(/^\d+[.)]\s*/, '')
          return (
            <li key={i} className="flex items-start gap-2 text-sm text-foreground/90">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-amber-500/15 text-amber-600 text-xs font-bold flex items-center justify-center mt-0.5">
                {i + 1}
              </span>
              <span className="leading-relaxed">{cleaned}</span>
            </li>
          )
        })}
      </ul>
    </BlockCard>
  )
}

/** Render a PROGRESS block with status-coded lines and a mini progress bar. */
function ProgressBlock({ content }: { content: string }) {
  const lines = content
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)

  // Classify each line by its prefix
  const items = lines.map((line) => {
    if (line.toUpperCase().startsWith('DONE:')) {
      return { status: 'done' as const, text: line.replace(/^DONE:\s*/i, '') }
    }
    if (line.toUpperCase().startsWith('IN PROGRESS:')) {
      return { status: 'in_progress' as const, text: line.replace(/^IN PROGRESS:\s*/i, '') }
    }
    if (line.toUpperCase().startsWith('TODO:')) {
      return { status: 'todo' as const, text: line.replace(/^TODO:\s*/i, '') }
    }
    // Unrecognized lines default to "todo"
    return { status: 'todo' as const, text: line }
  })

  const doneCount = items.filter((i) => i.status === 'done').length
  const totalCount = items.length
  const pct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0

  return (
    <BlockCard
      borderColor="border-l-4 border-l-cyan-500"
      icon={<TrendingUp size={14} className="text-cyan-500" />}
      title="Progress"
    >
      <ul className="space-y-1.5 mb-3">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            {item.status === 'done' && (
              <CheckCircle2 size={16} className="text-green-500 flex-shrink-0 mt-0.5" />
            )}
            {item.status === 'in_progress' && (
              <Loader2 size={16} className="text-cyan-500 animate-spin flex-shrink-0 mt-0.5" />
            )}
            {item.status === 'todo' && (
              <Circle size={16} className="text-muted-foreground flex-shrink-0 mt-0.5" />
            )}
            <span
              className={
                item.status === 'done'
                  ? 'text-foreground/70 line-through'
                  : item.status === 'in_progress'
                    ? 'text-foreground font-medium'
                    : 'text-foreground/80'
              }
            >
              {item.text}
            </span>
          </li>
        ))}
      </ul>

      {/* Mini progress bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-cyan-500 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-xs text-muted-foreground font-mono">
          {doneCount}/{totalCount}
        </span>
      </div>
    </BlockCard>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

/**
 * Render all structured notification blocks found in the given content.
 * Returns null when no blocks are present.
 */
export function AgentNotifications({ content, className }: AgentNotificationsProps): React.JSX.Element | null {
  const blocks = parseStructuredBlocks(content)

  if (blocks.length === 0) return null

  return (
    <div className={`flex flex-col gap-2 ${className ?? ''}`}>
      {blocks.map((block, i) => {
        switch (block.type) {
          case 'summary':
            return <SummaryBlock key={`summary-${i}`} content={block.content} />
          case 'roadmap':
            return <RoadmapBlock key={`roadmap-${i}`} content={block.content} />
          case 'progress':
            return <ProgressBlock key={`progress-${i}`} content={block.content} />
        }
      })}
    </div>
  )
}
