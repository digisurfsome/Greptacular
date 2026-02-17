/**
 * RepoBrowser
 *
 * Inline tree view for connected repos, rendered inside the Library panel.
 * Shows directory structure with expand/collapse and file preview on click.
 */

import { useState, useCallback, useMemo } from 'react'
import { ChevronRight, ChevronDown, Folder, FileText, RefreshCw, Unplug, GitBranch, Loader2 } from 'lucide-react'
import { useRepoTree, useSyncRepo, useDisconnectRepo } from '@/hooks/useWorkspaceLibrary'
import type { ConnectedRepo, RepoTreeEntry } from '@/lib/types'

interface RepoBrowserProps {
  repo: ConnectedRepo
  onFileClick?: (repoId: number, path: string) => void
}

interface TreeNode {
  name: string
  path: string
  type: 'file' | 'dir'
  size: number
  children: TreeNode[]
}

function buildTree(entries: RepoTreeEntry[]): TreeNode[] {
  const root: TreeNode[] = []
  const map = new Map<string, TreeNode>()

  // Sort entries so directories come before files at each level
  const sorted = [...entries].sort((a, b) => {
    if (a.type !== b.type) return a.type === 'dir' ? -1 : 1
    return a.path.localeCompare(b.path)
  })

  for (const entry of sorted) {
    const parts = entry.path.split('/')
    const name = parts[parts.length - 1]
    const node: TreeNode = { name, path: entry.path, type: entry.type, size: entry.size, children: [] }
    map.set(entry.path, node)

    if (parts.length === 1) {
      root.push(node)
    } else {
      const parentPath = parts.slice(0, -1).join('/')
      const parent = map.get(parentPath)
      if (parent) {
        parent.children.push(node)
      } else {
        root.push(node)
      }
    }
  }

  return root
}

function TreeItem({
  node,
  depth,
  expandedDirs,
  onToggleDir,
  onFileClick,
}: {
  node: TreeNode
  depth: number
  expandedDirs: Set<string>
  onToggleDir: (path: string) => void
  onFileClick?: (path: string) => void
}): React.JSX.Element {
  const isExpanded = expandedDirs.has(node.path)

  if (node.type === 'dir') {
    return (
      <>
        <button
          onClick={() => onToggleDir(node.path)}
          className="flex items-center gap-1.5 w-full py-1 text-sm hover:bg-muted/50 cursor-pointer text-foreground"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          <Folder size={14} className="text-muted-foreground" />
          <span className="truncate">{node.name}</span>
        </button>
        {isExpanded && node.children.map(child => (
          <TreeItem
            key={child.path}
            node={child}
            depth={depth + 1}
            expandedDirs={expandedDirs}
            onToggleDir={onToggleDir}
            onFileClick={onFileClick}
          />
        ))}
      </>
    )
  }

  return (
    <button
      onClick={() => onFileClick?.(node.path)}
      className="flex items-center gap-1.5 w-full py-1 text-sm hover:bg-muted/50 cursor-pointer text-foreground"
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
    >
      <span className="w-3" /> {/* spacer for alignment */}
      <FileText size={14} className="text-muted-foreground" />
      <span className="truncate">{node.name}</span>
    </button>
  )
}

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return 'never'
  const d = new Date(dateString)
  const now = new Date()
  const mins = Math.floor((now.getTime() - d.getTime()) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export function RepoBrowser({ repo, onFileClick }: RepoBrowserProps): React.JSX.Element {
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set())
  const { data: entries, isLoading } = useRepoTree(repo.id)
  const syncMut = useSyncRepo()
  const disconnectMut = useDisconnectRepo()

  const tree = useMemo(() => entries ? buildTree(entries) : [], [entries])

  const handleToggleDir = useCallback((path: string) => {
    setExpandedDirs(prev => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }, [])

  return (
    <div className="border border-border rounded-md overflow-hidden">
      {/* Repo header */}
      <div className="flex items-center justify-between px-3 py-2 bg-muted/30">
        <div className="flex items-center gap-2 min-w-0">
          <GitBranch size={14} className="text-muted-foreground flex-shrink-0" />
          <span className="text-sm font-medium text-foreground truncate">{repo.repo_name}</span>
          <span className="bg-muted text-muted-foreground text-xs px-2 py-0.5 rounded-md flex-shrink-0">
            {repo.branch}
          </span>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={() => syncMut.mutate(repo.id)}
            disabled={syncMut.isPending}
            className="p-1 rounded text-muted-foreground hover:text-foreground"
            title={`Synced ${formatRelativeTime(repo.last_synced_at)}`}
          >
            {syncMut.isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <RefreshCw size={14} />
            )}
          </button>
          <button
            onClick={() => {
              if (window.confirm('Disconnect this repository?')) {
                disconnectMut.mutate(repo.id)
              }
            }}
            className="p-1 rounded text-muted-foreground hover:text-destructive"
            title="Disconnect"
          >
            <Unplug size={14} />
          </button>
        </div>
      </div>

      {/* Tree */}
      <div className="max-h-60 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-4">
            <Loader2 size={14} className="animate-spin text-muted-foreground" />
          </div>
        ) : tree.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-3">Empty repository</p>
        ) : (
          tree.map(node => (
            <TreeItem
              key={node.path}
              node={node}
              depth={0}
              expandedDirs={expandedDirs}
              onToggleDir={handleToggleDir}
              onFileClick={onFileClick ? (path) => onFileClick(repo.id, path) : undefined}
            />
          ))
        )}
      </div>
    </div>
  )
}
