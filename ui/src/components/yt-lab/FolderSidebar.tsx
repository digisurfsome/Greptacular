import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Folder, Plus, Trash2, ChevronRight, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { listFolders, createFolder, deleteFolder } from '@/lib/api'
import type { YTFolder } from '@/lib/types'

interface FolderSidebarProps {
  selectedFolderId: number | null
  onSelectFolder: (folderId: number | null) => void
}

export default function FolderSidebar({ selectedFolderId, onSelectFolder }: FolderSidebarProps) {
  const queryClient = useQueryClient()
  const [newFolderName, setNewFolderName] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [expandedFolders, setExpandedFolders] = useState<Set<number>>(new Set())

  const { data: folders = [], isLoading } = useQuery({
    queryKey: ['yt-folders'],
    queryFn: listFolders,
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => createFolder(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['yt-folders'] })
      setNewFolderName('')
      setIsCreating(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteFolder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['yt-folders'] })
      if (selectedFolderId !== null) {
        onSelectFolder(null)
      }
    },
  })

  // Build folder tree from flat list
  const rootFolders = folders.filter((f: YTFolder) => f.parent_id === null)
  const getChildren = (parentId: number) => folders.filter((f: YTFolder) => f.parent_id === parentId)

  const toggleExpand = (folderId: number) => {
    setExpandedFolders(prev => {
      const next = new Set(prev)
      if (next.has(folderId)) next.delete(folderId)
      else next.add(folderId)
      return next
    })
  }

  const handleCreate = () => {
    if (newFolderName.trim()) {
      createMutation.mutate(newFolderName.trim())
    }
  }

  const renderFolder = (folder: YTFolder, depth: number = 0) => {
    const children = getChildren(folder.id)
    const hasChildren = children.length > 0
    const isExpanded = expandedFolders.has(folder.id)
    const isSelected = selectedFolderId === folder.id

    return (
      <div key={folder.id}>
        <div
          className={`group flex items-center gap-1 px-2 py-1.5 cursor-pointer rounded text-sm hover:bg-muted/50 ${
            isSelected ? 'bg-muted text-foreground font-medium' : 'text-muted-foreground'
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => onSelectFolder(folder.id)}
        >
          {hasChildren ? (
            <button
              onClick={(e) => { e.stopPropagation(); toggleExpand(folder.id) }}
              className="p-0.5 hover:bg-muted rounded"
            >
              {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            </button>
          ) : (
            <span className="w-4" />
          )}
          <Folder className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate flex-1">{folder.name}</span>
          <button
            onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(folder.id) }}
            className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-400"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
        {hasChildren && isExpanded && children.map((child: YTFolder) => renderFolder(child, depth + 1))}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full border-r border-border bg-card/50">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-xs font-semibold uppercase text-muted-foreground">Folders</span>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setIsCreating(!isCreating)}>
          <Plus className="h-3.5 w-3.5" />
        </Button>
      </div>

      {isCreating && (
        <div className="flex gap-1 px-2 py-2 border-b border-border">
          <Input
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="Folder name"
            className="h-7 text-xs"
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            autoFocus
          />
          <Button size="sm" className="h-7 px-2 text-xs" onClick={handleCreate} disabled={createMutation.isPending}>
            Add
          </Button>
        </div>
      )}

      <div className="flex-1 overflow-auto py-1">
        {/* All Videos option */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 cursor-pointer rounded text-sm hover:bg-muted/50 ${
            selectedFolderId === null ? 'bg-muted text-foreground font-medium' : 'text-muted-foreground'
          }`}
          onClick={() => onSelectFolder(null)}
        >
          <Folder className="h-3.5 w-3.5" />
          <span>All Videos</span>
        </div>

        {isLoading ? (
          <div className="px-3 py-2 text-xs text-muted-foreground">Loading...</div>
        ) : (
          rootFolders.map((folder: YTFolder) => renderFolder(folder))
        )}
      </div>
    </div>
  )
}
