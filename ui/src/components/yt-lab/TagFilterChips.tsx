import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, X, Tag } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { listTags, createTag, deleteTag } from '@/lib/api'
import type { YTTag } from '@/lib/types'

interface TagFilterChipsProps {
  selectedTagIds: number[]
  onToggleTag: (tagId: number) => void
}

export default function TagFilterChips({ selectedTagIds, onToggleTag }: TagFilterChipsProps) {
  const queryClient = useQueryClient()
  const [isAdding, setIsAdding] = useState(false)
  const [newTagName, setNewTagName] = useState('')

  const { data: tags = [] } = useQuery({
    queryKey: ['yt-tags'],
    queryFn: listTags,
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => createTag(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['yt-tags'] })
      setNewTagName('')
      setIsAdding(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteTag(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['yt-tags'] })
    },
  })

  const handleCreate = () => {
    if (newTagName.trim()) {
      createMutation.mutate(newTagName.trim())
    }
  }

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <Tag className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      {tags.map((tag: YTTag) => {
        const isSelected = selectedTagIds.includes(tag.id)
        return (
          <Badge
            key={tag.id}
            variant={isSelected ? 'default' : 'outline'}
            className="cursor-pointer text-xs gap-1 hover:bg-muted"
            onClick={() => onToggleTag(tag.id)}
          >
            {tag.name}
            <button
              onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(tag.id) }}
              className="ml-0.5 hover:text-red-400"
            >
              <X className="h-2.5 w-2.5" />
            </button>
          </Badge>
        )
      })}

      {isAdding ? (
        <div className="flex items-center gap-1">
          <Input
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            placeholder="Tag name"
            className="h-6 w-24 text-xs"
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            autoFocus
          />
          <Button size="sm" className="h-6 px-2 text-xs" onClick={handleCreate}>
            Add
          </Button>
          <Button size="sm" variant="ghost" className="h-6 px-1 text-xs" onClick={() => setIsAdding(false)}>
            <X className="h-3 w-3" />
          </Button>
        </div>
      ) : (
        <Button variant="ghost" size="sm" className="h-6 px-1.5 text-xs" onClick={() => setIsAdding(true)}>
          <Plus className="h-3 w-3" />
        </Button>
      )}
    </div>
  )
}
