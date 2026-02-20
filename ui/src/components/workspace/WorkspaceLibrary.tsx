/**
 * WorkspaceLibrary
 *
 * Right-hand panel that manages the file library and GitHub repo connections.
 * Files can be toggled into the active context for the current conversation.
 * Split into two tabs: Library (files) and Repos (GitHub connections).
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import {
  FileText,
  GitBranch,
  Upload,
  ClipboardPaste,
  Plus,
  ToggleLeft,
  ToggleRight,
  Eye,
  Trash2,
  Globe,
  MessageSquare,
  Radio,
  User,
  Bot,
  Info,
} from 'lucide-react'
import {
  useConversationFiles,
  useGlobalFiles,
  useToggleFile,
  useDeleteFile,
  useConnectedRepos,
} from '@/hooks/useWorkspaceLibrary'
import { FileUploadModal } from './FileUploadModal'
import { FilePreview } from './FilePreview'
import { RepoConnector } from './RepoConnector'
import { RepoBrowser } from './RepoBrowser'
import { getRepoFile } from '@/lib/api'
import { Button } from '@/components/ui/button'
import type { LibraryFile, WalkieTalkieLogEntry } from '@/lib/types'

interface WorkspaceLibraryProps {
  conversationId: number | null
  collapsed: boolean
  onToggleCollapse: () => void
  walkieTalkieLog?: WalkieTalkieLogEntry[]
}

type Tab = 'library' | 'repos' | 'walkie-talkie'

const TYPE_COLORS: Record<string, string> = {
  doc: 'bg-blue-500/10 text-blue-500',
  code: 'bg-green-500/10 text-green-500',
  spec: 'bg-purple-500/10 text-purple-500',
  template: 'bg-orange-500/10 text-orange-500',
  upload: 'bg-muted text-muted-foreground',
}

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)}M`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)}K`
  return `${bytes}B`
}

export function WorkspaceLibrary({
  conversationId,
  collapsed,
  onToggleCollapse,
  walkieTalkieLog = [],
}: WorkspaceLibraryProps): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>('library')
  const wtLogEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll walkie-talkie log to bottom when new entries arrive
  useEffect(() => {
    if (activeTab === 'walkie-talkie') {
      wtLogEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [walkieTalkieLog.length, activeTab])
  const [uploadModal, setUploadModal] = useState<'file' | 'text' | null>(null)
  const [repoModal, setRepoModal] = useState(false)
  const [previewFile, setPreviewFile] = useState<LibraryFile | null>(null)
  const [repoFilePreview, setRepoFilePreview] = useState<{ content: string; path: string } | null>(null)

  // Queries
  const { data: globalFiles = [] } = useGlobalFiles()
  const { data: conversationFiles } = useConversationFiles(conversationId)
  const { data: repos = [] } = useConnectedRepos(conversationId)

  // Mutations
  const toggleFile = useToggleFile(conversationId ?? 0)
  const deleteFile = useDeleteFile()

  // Use conversation-scoped files list when a conversation is active, otherwise global
  const files: LibraryFile[] = conversationFiles ?? globalFiles

  const handleToggle = useCallback((fileId: number) => {
    if (!conversationId) return
    toggleFile.mutate(fileId)
  }, [conversationId, toggleFile])

  const handleDelete = useCallback((fileId: number) => {
    if (window.confirm('Delete this file from the library?')) {
      deleteFile.mutate(fileId)
      if (previewFile?.id === fileId) setPreviewFile(null)
    }
  }, [deleteFile, previewFile])

  const handleRepoFileClick = useCallback(async (repoId: number, path: string) => {
    try {
      const result = await getRepoFile(repoId, path)
      setRepoFilePreview(result)
    } catch {
      // Non-text file or not found
    }
  }, [])

  if (collapsed) {
    return (
      <div className="w-10 border-l border-border bg-card flex flex-col items-center py-3 gap-3">
        <button onClick={onToggleCollapse} className="text-muted-foreground hover:text-foreground" title="Expand Library">
          <FileText size={16} />
        </button>
      </div>
    )
  }

  return (
    <div className="w-72 border-l border-border bg-card flex flex-col">
      {/* Tab bar */}
      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab('library')}
          className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
            activeTab === 'library'
              ? 'text-foreground border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <FileText size={14} />
          Library
        </button>
        <button
          onClick={() => setActiveTab('repos')}
          className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
            activeTab === 'repos'
              ? 'text-foreground border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <GitBranch size={14} />
          Repos
          {repos.length > 0 && (
            <span className="bg-muted text-muted-foreground text-xs px-1.5 rounded-full">{repos.length}</span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('walkie-talkie')}
          className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
            activeTab === 'walkie-talkie'
              ? 'text-amber-600 dark:text-amber-400 border-b-2 border-amber-500'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Radio size={14} />
          WT
          {walkieTalkieLog.length > 0 && (
            <span className="bg-amber-500/20 text-amber-600 dark:text-amber-400 text-[10px] px-1.5 rounded-full font-bold">
              {walkieTalkieLog.length}
            </span>
          )}
        </button>
        <button
          onClick={onToggleCollapse}
          className="px-2 text-muted-foreground hover:text-foreground"
          title="Collapse"
        >
          &raquo;
        </button>
      </div>

      {/* Library tab */}
      {activeTab === 'library' && (
        <>
          {/* Upload actions */}
          <div className="flex gap-1 px-2 py-2 border-b border-border">
            <Button variant="outline" size="sm" className="flex-1 gap-1 text-xs" onClick={() => setUploadModal('file')}>
              <Upload size={12} /> Upload
            </Button>
            <Button variant="outline" size="sm" className="flex-1 gap-1 text-xs" onClick={() => setUploadModal('text')}>
              <ClipboardPaste size={12} /> Paste
            </Button>
          </div>

          {/* File list */}
          <div className="flex-1 overflow-y-auto">
            {files.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground text-xs">
                <FileText size={20} strokeWidth={1.5} />
                <span>No files yet</span>
              </div>
            ) : (
              <div className="py-1">
                {files.map(file => (
                  <div
                    key={file.id}
                    className="group flex items-center gap-2 px-2 py-1.5 hover:bg-muted/50"
                  >
                    {/* Toggle active */}
                    <button
                      onClick={() => handleToggle(file.id)}
                      disabled={!conversationId}
                      className={`flex-shrink-0 ${conversationId ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}`}
                      title={file.active_in_context ? 'Remove from context' : 'Add to context'}
                    >
                      {file.active_in_context ? (
                        <ToggleRight size={16} className="text-primary" />
                      ) : (
                        <ToggleLeft size={16} className="text-muted-foreground" />
                      )}
                    </button>

                    {/* File info */}
                    <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setPreviewFile(file)}>
                      <div className="flex items-center gap-1.5">
                        <span className={`px-1 py-0.5 rounded text-[10px] font-medium ${TYPE_COLORS[file.file_type] || TYPE_COLORS.upload}`}>
                          {file.file_type}
                        </span>
                        <span className="text-xs text-foreground truncate">
                          {file.display_name || file.filename}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        {file.conversation_id === null ? (
                          <Globe size={10} className="text-muted-foreground" />
                        ) : (
                          <MessageSquare size={10} className="text-muted-foreground" />
                        )}
                        <span className="text-[10px] text-muted-foreground">{formatSize(file.file_size)}</span>
                        {file.tags && (
                          <span className="text-[10px] text-muted-foreground truncate">{file.tags}</span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100">
                      <button onClick={() => setPreviewFile(file)} className="p-1 text-muted-foreground hover:text-foreground">
                        <Eye size={12} />
                      </button>
                      <button onClick={() => handleDelete(file.id)} className="p-1 text-muted-foreground hover:text-destructive">
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Repos tab */}
      {activeTab === 'repos' && (
        <>
          {/* Connect action */}
          <div className="px-2 py-2 border-b border-border">
            <Button variant="outline" size="sm" className="w-full gap-1 text-xs" onClick={() => setRepoModal(true)}>
              <Plus size={12} /> Connect Repository
            </Button>
          </div>

          {/* Repos list */}
          <div className="flex-1 overflow-y-auto px-2 py-2 space-y-2">
            {repos.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground text-xs">
                <GitBranch size={20} strokeWidth={1.5} />
                <span>No repos connected</span>
              </div>
            ) : (
              repos.map(repo => (
                <RepoBrowser key={repo.id} repo={repo} onFileClick={handleRepoFileClick} />
              ))
            )}
          </div>
        </>
      )}

      {/* Walkie-Talkie tab */}
      {activeTab === 'walkie-talkie' && (
        <div className="flex-1 overflow-y-auto">
          {walkieTalkieLog.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground text-xs">
              <Radio size={20} strokeWidth={1.5} className="text-amber-500/50" />
              <span>No walkie-talkie messages yet</span>
              <span className="text-[10px] text-center px-4">
                Messages you send via the amber bar while the agent is working will appear here.
              </span>
            </div>
          ) : (
            <div className="py-2 space-y-1">
              {walkieTalkieLog.map((entry) => (
                <div
                  key={entry.id}
                  className={`mx-2 px-2.5 py-1.5 rounded-lg text-xs ${
                    entry.sender === 'user'
                      ? 'bg-amber-500/10 border border-amber-500/20'
                      : entry.sender === 'agent'
                        ? 'bg-primary/5 border border-primary/10'
                        : 'bg-muted/50'
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-0.5">
                    {entry.sender === 'user' ? (
                      <User size={10} className="text-amber-600 dark:text-amber-400" />
                    ) : entry.sender === 'agent' ? (
                      <Bot size={10} className="text-primary" />
                    ) : (
                      <Info size={10} className="text-muted-foreground" />
                    )}
                    <span className={`text-[10px] font-semibold ${
                      entry.sender === 'user'
                        ? 'text-amber-600 dark:text-amber-400'
                        : entry.sender === 'agent'
                          ? 'text-primary'
                          : 'text-muted-foreground'
                    }`}>
                      {entry.sender === 'user' ? 'You' : entry.sender === 'agent' ? 'Agent' : 'System'}
                    </span>
                    <span className="text-[10px] text-muted-foreground ml-auto">
                      {entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-foreground leading-snug break-words">{entry.content}</p>
                </div>
              ))}
              <div ref={wtLogEndRef} />
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      {uploadModal && (
        <FileUploadModal
          open
          onClose={() => setUploadModal(null)}
          conversationId={conversationId}
          mode={uploadModal}
        />
      )}
      {repoModal && (
        <RepoConnector
          open
          onClose={() => setRepoModal(false)}
          conversationId={conversationId}
        />
      )}
      {previewFile && (
        <FilePreview
          fileId={previewFile.id}
          fileName={previewFile.display_name || previewFile.filename}
          fileType={previewFile.file_type}
          onClose={() => setPreviewFile(null)}
          onToggleContext={conversationId ? () => handleToggle(previewFile.id) : undefined}
          onDelete={() => handleDelete(previewFile.id)}
          isActive={previewFile.active_in_context}
        />
      )}
      {repoFilePreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-card border border-border rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <span className="text-sm font-medium text-foreground truncate">{repoFilePreview.path}</span>
              <button onClick={() => setRepoFilePreview(null)} className="text-muted-foreground hover:text-foreground">
                &times;
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <pre className="bg-muted rounded-lg p-4 overflow-x-auto font-mono text-sm text-foreground whitespace-pre-wrap">
                {repoFilePreview.content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
