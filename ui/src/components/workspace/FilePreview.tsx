/**
 * FilePreview
 *
 * Modal for viewing file content from the workspace library.
 * Renders markdown files with prose styling and code files with monospace.
 */

import { X, ToggleLeft, ToggleRight, Trash2, Loader2 } from 'lucide-react'
import { useFileContent } from '@/hooks/useWorkspaceLibrary'
import { Button } from '@/components/ui/button'

interface FilePreviewProps {
  fileId: number
  fileName: string
  fileType: string
  onClose: () => void
  onToggleContext?: () => void
  onDelete?: () => void
  isActive?: boolean
}

const CODE_EXTENSIONS = new Set([
  'code', 'spec',
])

export function FilePreview({
  fileId,
  fileName,
  fileType,
  onClose,
  onToggleContext,
  onDelete,
  isActive = false,
}: FilePreviewProps): React.JSX.Element {
  const { data, isLoading } = useFileContent(fileId)
  const content = data?.content ?? ''
  const isCode = CODE_EXTENSIONS.has(fileType) || fileName.match(/\.(py|js|ts|tsx|jsx|rs|go|java|c|cpp|rb|php|sh|sql|css|html|json|yaml|yml|xml|toml)$/)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card border border-border rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <span className="text-sm font-medium text-foreground truncate">{fileName}</span>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-border">
          {onToggleContext && (
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleContext}
              className="gap-1.5"
            >
              {isActive ? <ToggleRight size={14} /> : <ToggleLeft size={14} />}
              {isActive ? 'Remove from Context' : 'Add to Context'}
            </Button>
          )}
          {onDelete && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDelete}
              className="gap-1.5 text-destructive hover:text-destructive"
            >
              <Trash2 size={14} />
              Delete
            </Button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 size={20} className="animate-spin text-muted-foreground" />
            </div>
          ) : isCode ? (
            <pre className="bg-muted rounded-lg p-4 overflow-x-auto font-mono text-sm text-foreground whitespace-pre-wrap">
              {content}
            </pre>
          ) : fileType === 'doc' ? (
            <div className="chat-prose text-sm text-foreground whitespace-pre-wrap">
              {content}
            </div>
          ) : (
            <pre className="text-sm text-foreground whitespace-pre-wrap">
              {content}
            </pre>
          )}
        </div>
      </div>
    </div>
  )
}
