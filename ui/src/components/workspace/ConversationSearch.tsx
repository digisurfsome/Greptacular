/**
 * ConversationSearch
 *
 * Search input that upgrades to server-side search when the query
 * is 3+ characters. Shows results with highlighted excerpts.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { Search, X, MessageSquare } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { searchWorkspaceConversations } from '@/lib/api'

interface ConversationSearchProps {
  onSelectConversation: (conversationId: number) => void
  onFilterChange: (filter: string) => void
}

/** Escape regex special characters in a string. */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Highlight matching text in an excerpt. */
function HighlightedExcerpt({ text, query }: { text: string; query: string }): React.JSX.Element {
  const regex = new RegExp(`(${escapeRegex(query)})`, 'gi')
  const parts = text.split(regex)
  return (
    <>
      {parts.map((part, i) =>
        regex.test(part)
          ? <mark key={i} className="bg-primary/20 text-foreground rounded px-0.5">{part}</mark>
          : <span key={i}>{part}</span>
      )}
    </>
  )
}

/** Server-side search input with results overlay. */
export function ConversationSearch({
  onSelectConversation,
  onFilterChange,
}: ConversationSearchProps): React.JSX.Element {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [showResults, setShowResults] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Debounce the search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  // Update client-side filter for short queries
  useEffect(() => {
    if (query.length < 3) {
      onFilterChange(query)
    }
  }, [query, onFilterChange])

  // Server-side search for queries >= 3 characters
  const { data: searchResults } = useQuery({
    queryKey: ['workspace', 'search', debouncedQuery],
    queryFn: () => searchWorkspaceConversations(debouncedQuery),
    enabled: debouncedQuery.length >= 3,
  })

  // Close results when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowResults(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setQuery('')
      setShowResults(false)
      onFilterChange('')
    }
  }, [onFilterChange])

  const handleClear = useCallback(() => {
    setQuery('')
    setShowResults(false)
    onFilterChange('')
  }, [onFilterChange])

  const handleSelect = useCallback((conversationId: number) => {
    onSelectConversation(conversationId)
    setShowResults(false)
    setQuery('')
    onFilterChange('')
  }, [onSelectConversation, onFilterChange])

  const hasResults = debouncedQuery.length >= 3 && searchResults && searchResults.length > 0

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search
          size={14}
          className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setShowResults(true) }}
          onFocus={() => setShowResults(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search conversations..."
          className="w-full pl-8 pr-8 py-1.5 text-xs border border-border rounded bg-input text-foreground placeholder:text-muted-foreground outline-none ring-ring focus:ring-1"
          aria-label="Search conversations"
        />
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X size={12} />
          </button>
        )}
      </div>

      {showResults && hasResults && (
        <div className="absolute top-full left-0 right-0 z-20 mt-1 max-h-64 overflow-y-auto bg-popover border border-border rounded-md shadow-md">
          {searchResults.map((result) => (
            <button
              key={result.conversation_id}
              onClick={() => handleSelect(result.conversation_id)}
              className="w-full text-left px-3 py-2 hover:bg-accent transition-colors border-b border-border last:border-b-0"
            >
              <div className="flex items-center gap-2">
                <MessageSquare size={12} className="text-muted-foreground flex-shrink-0" />
                <span className="text-xs font-medium text-foreground truncate">
                  {result.conversation_title || 'Untitled'}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-secondary text-secondary-foreground">
                  {result.category}
                </span>
              </div>
              {result.matching_excerpts.slice(0, 2).map((excerpt, i) => (
                <div key={i} className="mt-1 text-[11px] text-muted-foreground line-clamp-1">
                  <HighlightedExcerpt text={excerpt.excerpt} query={debouncedQuery} />
                </div>
              ))}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
