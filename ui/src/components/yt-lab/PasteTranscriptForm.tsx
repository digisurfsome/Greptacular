import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ClipboardPaste, Link, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { saveTranscript } from '@/lib/api'

interface PasteTranscriptFormProps {
  onSaved?: (videoId: string) => void
}

export default function PasteTranscriptForm({ onSaved }: PasteTranscriptFormProps) {
  const [mode, setMode] = useState<'url' | 'paste'>('paste')
  const [videoId, setVideoId] = useState('')
  const [title, setTitle] = useState('')
  const [transcriptText, setTranscriptText] = useState('')

  const saveMutation = useMutation({
    mutationFn: () => {
      const id = videoId.trim() || `paste_${Date.now()}`
      return saveTranscript(id, transcriptText, title || undefined, 'paste')
    },
    onSuccess: (data) => {
      setVideoId('')
      setTitle('')
      setTranscriptText('')
      onSaved?.(data.video_id)
    },
  })

  const handleSubmit = () => {
    if (!transcriptText.trim()) return
    saveMutation.mutate()
  }

  return (
    <div className="space-y-3 p-4 border border-border rounded-lg bg-card">
      <div className="flex items-center gap-2">
        <ClipboardPaste className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold">Paste Transcript</h3>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-1">
        <Button
          size="sm"
          variant={mode === 'paste' ? 'default' : 'outline'}
          className="h-7 text-xs gap-1"
          onClick={() => setMode('paste')}
        >
          <FileText className="h-3 w-3" /> Paste Text
        </Button>
        <Button
          size="sm"
          variant={mode === 'url' ? 'default' : 'outline'}
          className="h-7 text-xs gap-1"
          onClick={() => setMode('url')}
        >
          <Link className="h-3 w-3" /> From URL
        </Button>
      </div>

      {mode === 'url' && (
        <div className="space-y-1.5">
          <Label className="text-xs">Video ID or URL</Label>
          <Input
            value={videoId}
            onChange={(e) => setVideoId(e.target.value)}
            placeholder="e.g. dQw4w9WgXcQ or full YouTube URL"
            className="h-8 text-sm"
          />
        </div>
      )}

      <div className="space-y-1.5">
        <Label className="text-xs">Title (optional)</Label>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Video or source title"
          className="h-8 text-sm"
        />
      </div>

      <div className="space-y-1.5">
        <Label className="text-xs">Transcript</Label>
        <Textarea
          value={transcriptText}
          onChange={(e) => setTranscriptText(e.target.value)}
          placeholder="Paste the full transcript here..."
          rows={8}
          className="text-sm resize-none"
        />
        {transcriptText && (
          <p className="text-xs text-muted-foreground">
            {transcriptText.length.toLocaleString()} characters
          </p>
        )}
      </div>

      <Button
        onClick={handleSubmit}
        disabled={!transcriptText.trim() || saveMutation.isPending}
        className="w-full"
        size="sm"
      >
        {saveMutation.isPending ? 'Saving...' : 'Save Transcript'}
      </Button>

      {saveMutation.isError && (
        <p className="text-xs text-red-400">
          {saveMutation.error instanceof Error ? saveMutation.error.message : 'Failed to save'}
        </p>
      )}

      {saveMutation.isSuccess && (
        <p className="text-xs text-green-400">Transcript saved successfully</p>
      )}
    </div>
  )
}
