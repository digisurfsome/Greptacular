/**
 * RepoConnector
 *
 * Modal for connecting a GitHub repository to the workspace.
 * Handles URL validation, token input, and clone progress.
 */

import { useState, useCallback } from 'react'
import { X, Loader2 } from 'lucide-react'
import { useConnectRepo } from '@/hooks/useWorkspaceLibrary'
import { Button } from '@/components/ui/button'

interface RepoConnectorProps {
  open: boolean
  onClose: () => void
  conversationId: number | null
}

const GITHUB_URL_PATTERN = /^https:\/\/github\.com\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+(\.git)?$/

export function RepoConnector({
  open,
  onClose,
  conversationId,
}: RepoConnectorProps): React.JSX.Element | null {
  const [repoUrl, setRepoUrl] = useState('')
  const [token, setToken] = useState('')
  const [branch, setBranch] = useState('main')
  const [scope, setScope] = useState<'global' | 'chat'>('global')
  const [urlError, setUrlError] = useState('')
  const [error, setError] = useState('')

  const connectRepo = useConnectRepo()

  const handleUrlBlur = useCallback(() => {
    if (repoUrl && !GITHUB_URL_PATTERN.test(repoUrl)) {
      setUrlError('Must be a GitHub HTTPS URL (https://github.com/owner/repo)')
    } else {
      setUrlError('')
    }
  }, [repoUrl])

  const handleConnect = useCallback(async () => {
    setError('')
    if (!GITHUB_URL_PATTERN.test(repoUrl)) {
      setUrlError('Must be a GitHub HTTPS URL')
      return
    }
    if (!token) {
      setError('Personal access token is required')
      return
    }

    try {
      await connectRepo.mutateAsync({
        repoUrl,
        token,
        branch,
        conversationId: scope === 'chat' ? (conversationId ?? undefined) : undefined,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect repository')
    }
  }, [repoUrl, token, branch, scope, conversationId, connectRepo, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card border border-border rounded-lg shadow-lg p-6 max-w-lg w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-foreground">Connect GitHub Repository</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Repository URL</label>
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => { setRepoUrl(e.target.value); setUrlError('') }}
              onBlur={handleUrlBlur}
              className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm text-foreground"
              placeholder="https://github.com/owner/repo"
            />
            {urlError && <p className="text-xs text-destructive mt-1">{urlError}</p>}
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Personal Access Token</label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm text-foreground"
              placeholder="ghp_..."
            />
            <p className="text-xs text-muted-foreground mt-1">
              Fine-grained token with repo read access
            </p>
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Branch</label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm text-foreground"
              placeholder="main"
            />
          </div>

          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Scope</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-1.5 text-sm text-foreground">
                <input type="radio" name="repo-scope" checked={scope === 'global'} onChange={() => setScope('global')} />
                Global
              </label>
              <label className={`flex items-center gap-1.5 text-sm ${conversationId ? 'text-foreground' : 'text-muted-foreground'}`}>
                <input type="radio" name="repo-scope" checked={scope === 'chat'} onChange={() => setScope('chat')} disabled={!conversationId} />
                This Chat
              </label>
            </div>
          </div>
        </div>

        {error && <p className="text-sm text-destructive mt-3">{error}</p>}

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={onClose} disabled={connectRepo.isPending}>
            Cancel
          </Button>
          <Button onClick={handleConnect} disabled={connectRepo.isPending || !repoUrl || !token}>
            {connectRepo.isPending ? (
              <>
                <Loader2 size={14} className="animate-spin mr-1" />
                Cloning...
              </>
            ) : (
              'Connect'
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
