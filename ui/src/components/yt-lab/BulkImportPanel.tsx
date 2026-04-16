import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Upload, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { createBatchJob, listBatchJobs } from '@/lib/api'
import type { YTBatchJob, YTBatchItem } from '@/lib/types'

export default function BulkImportPanel() {
  const queryClient = useQueryClient()
  const [urlText, setUrlText] = useState('')

  const { data: jobs = [] } = useQuery({
    queryKey: ['yt-batch-jobs'],
    queryFn: listBatchJobs,
    refetchInterval: jobs?.some((j: YTBatchJob) => ['pending', 'running'].includes(j.status)) ? 5000 : false,
  })

  const createMutation = useMutation({
    mutationFn: (urls: string[]) => createBatchJob(urls),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['yt-batch-jobs'] })
      setUrlText('')
    },
  })

  const handleSubmit = () => {
    const urls = urlText
      .split('\n')
      .map(u => u.trim())
      .filter(u => u.length > 0)
    if (urls.length === 0) return
    createMutation.mutate(urls)
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case 'complete': return <CheckCircle className="h-3.5 w-3.5 text-green-400" />
      case 'failed': return <XCircle className="h-3.5 w-3.5 text-red-400" />
      case 'running':
      case 'processing': return <Loader2 className="h-3.5 w-3.5 text-blue-400 animate-spin" />
      default: return <Clock className="h-3.5 w-3.5 text-muted-foreground" />
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'bg-green-500/20 text-green-400'
      case 'failed': return 'bg-red-500/20 text-red-400'
      case 'running': return 'bg-blue-500/20 text-blue-400'
      default: return 'bg-muted text-muted-foreground'
    }
  }

  const urlCount = urlText.split('\n').filter(u => u.trim()).length

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center gap-2">
        <Upload className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold">Bulk Import</h3>
      </div>

      {/* URL Input */}
      <div className="space-y-2">
        <Textarea
          value={urlText}
          onChange={(e) => setUrlText(e.target.value)}
          placeholder="Paste YouTube URLs (one per line)..."
          rows={5}
          className="text-sm resize-none font-mono"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">{urlCount} URL{urlCount !== 1 ? 's' : ''}</span>
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={urlCount === 0 || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : `Import ${urlCount} URL${urlCount !== 1 ? 's' : ''}`}
          </Button>
        </div>
      </div>

      {createMutation.isError && (
        <p className="text-xs text-red-400">
          {createMutation.error instanceof Error ? createMutation.error.message : 'Import failed'}
        </p>
      )}

      {/* Job History */}
      {jobs.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">Import Jobs</h4>
          {jobs.map((job: YTBatchJob) => (
            <div key={job.id} className="p-2.5 rounded border border-border bg-card space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {statusIcon(job.status)}
                  <span className="text-sm font-medium">Job #{job.id}</span>
                  <Badge variant="outline" className={`text-[10px] ${statusColor(job.status)}`}>
                    {job.status}
                  </Badge>
                </div>
                <span className="text-xs text-muted-foreground">
                  {job.processed}/{job.total_urls}
                  {job.failed > 0 && <span className="text-red-400 ml-1">({job.failed} failed)</span>}
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all"
                  style={{ width: `${job.total_urls > 0 ? (job.processed / job.total_urls) * 100 : 0}%` }}
                />
              </div>

              {/* Item list (collapsed by default, show failures) */}
              {job.items?.filter((i: YTBatchItem) => i.status === 'failed').length > 0 && (
                <div className="space-y-0.5">
                  {job.items
                    .filter((i: YTBatchItem) => i.status === 'failed')
                    .map((item: YTBatchItem) => (
                      <div key={item.id} className="text-xs text-red-400/80 flex items-center gap-1">
                        <XCircle className="h-2.5 w-2.5" />
                        <span className="truncate">{item.url}</span>
                        {item.error && <span className="text-red-400/50">— {item.error}</span>}
                      </div>
                    ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
