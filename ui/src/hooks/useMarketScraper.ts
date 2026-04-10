import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../lib/api'
import type { TopicSearchParams } from '../lib/api'

export function useScrapes() {
  return useQuery({
    queryKey: ['market-scraper', 'scrapes'],
    queryFn: api.getMarketScrapes,
  })
}

export function useScrape(id: number | null) {
  return useQuery({
    queryKey: ['market-scraper', 'scrape', id],
    queryFn: () => api.getMarketScrape(id!),
    enabled: id !== null,
  })
}

export function useScrapeThread() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (url: string) => api.scrapeRedditThread(url),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['market-scraper'] })
    },
  })
}

export function useDeleteScrape() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.deleteMarketScrape(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['market-scraper'] })
    },
  })
}

export function useSearchOptions() {
  return useQuery({
    queryKey: ['market-scraper', 'search-options'],
    queryFn: api.getSearchOptions,
  })
}

export function useSearchReddit() {
  return useMutation({
    mutationFn: (params: TopicSearchParams) => api.searchReddit(params),
  })
}

export function useSearchAndScrape() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (params: TopicSearchParams) => api.searchAndScrapeReddit(params),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['market-scraper'] })
    },
  })
}

export function usePhraseFrequency(params?: {
  scrape_ids?: number[]
  category?: string
  top_n?: number
}) {
  return useQuery({
    queryKey: ['market-scraper', 'phrase-frequency', params],
    queryFn: () => api.getPhraseFrequency(params),
    // Only fetch when there's at least one scrape to analyze
    enabled: true,
  })
}
