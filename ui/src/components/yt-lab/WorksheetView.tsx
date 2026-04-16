import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { CheckSquare, Square, Loader2, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getWorksheet, generateWorksheet } from '@/lib/api'
import type { YTWorksheetItem } from '@/lib/types'

interface WorksheetViewProps {
  videoId: string
  transcriptText?: string
}

export default function WorksheetView({ videoId, transcriptText }: WorksheetViewProps) {
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set())

  const { data: worksheet, isLoading, refetch } = useQuery({
    queryKey: ['yt-worksheet', videoId],
    queryFn: () => getWorksheet(videoId),
    retry: false,
  })

  const generateMutation = useMutation({
    mutationFn: () => {
      if (!transcriptText) throw new Error('No transcript available')
      return generateWorksheet(videoId, transcriptText)
    },
    onSuccess: () => refetch(),
  })

  const toggleItem = (order: number) => {
    setCheckedItems(prev => {
      const next = new Set(prev)
      if (next.has(order)) next.delete(order)
      else next.add(order)
      return next
    })
  }

  const difficultyColor = (d: string) => {
    switch (d) {
      case 'easy': return 'bg-green-500/20 text-green-400'
      case 'medium': return 'bg-yellow-500/20 text-yellow-400'
      case 'hard': return 'bg-red-500/20 text-red-400'
      default: return 'bg-muted text-muted-foreground'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading worksheet...
      </div>
    )
  }

  if (!worksheet) {
    return (
      <div className="p-4 space-y-3">
        <p className="text-sm text-muted-foreground">No worksheet generated yet.</p>
        {transcriptText && (
          <Button
            size="sm"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="gap-1.5"
          >
            {generateMutation.isPending ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Generating...</>
            ) : (
              <><Sparkles className="h-3.5 w-3.5" /> Generate Worksheet</>
            )}
          </Button>
        )}
        {generateMutation.isError && (
          <p className="text-xs text-red-400">
            {generateMutation.error instanceof Error ? generateMutation.error.message : 'Generation failed'}
          </p>
        )}
      </div>
    )
  }

  const data = worksheet.data
  const completedCount = checkedItems.size
  const totalCount = data.action_items?.length || 0

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{data.title || 'Worksheet'}</h3>
        <span className="text-xs text-muted-foreground">
          {completedCount}/{totalCount} complete
        </span>
      </div>

      {data.prerequisites?.length > 0 && (
        <div className="text-xs text-muted-foreground">
          <span className="font-medium">Prerequisites:</span> {data.prerequisites.join(', ')}
        </div>
      )}

      <div className="space-y-2">
        {data.action_items?.map((item: YTWorksheetItem) => {
          const isChecked = checkedItems.has(item.order)
          return (
            <div
              key={item.order}
              className={`flex gap-2 p-2.5 rounded border border-border cursor-pointer transition-colors ${
                isChecked ? 'bg-green-500/5 border-green-500/20' : 'bg-card hover:bg-muted/30'
              }`}
              onClick={() => toggleItem(item.order)}
            >
              <div className="pt-0.5">
                {isChecked ? (
                  <CheckSquare className="h-4 w-4 text-green-400" />
                ) : (
                  <Square className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${isChecked ? 'line-through text-muted-foreground' : ''}`}>
                    {item.title}
                  </span>
                  <Badge variant="outline" className={`text-[10px] ${difficultyColor(item.difficulty)}`}>
                    {item.difficulty}
                  </Badge>
                  {item.time_estimate && (
                    <span className="text-[10px] text-muted-foreground">{item.time_estimate}</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{item.description}</p>
                {item.tools_needed?.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {item.tools_needed.map((tool, i) => (
                      <Badge key={i} variant="outline" className="text-[10px]">{tool}</Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {data.estimated_total_time && (
        <p className="text-xs text-muted-foreground">
          Estimated total time: {data.estimated_total_time}
        </p>
      )}
    </div>
  )
}
