import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listBlueprints,
  listBlueprintCategories,
  getBlueprint,
  createBlueprint,
  updateBlueprint,
  deleteBlueprint,
} from '@/lib/api'
import type { RoleBlueprintCreate, RoleBlueprintUpdate } from '@/lib/types'

const ALL_KEYS = ['workspace', 'roles'] as const

const KEYS = {
  all: ALL_KEYS,
  list: (category?: string) => [...ALL_KEYS, 'list', category] as const,
  categories: [...ALL_KEYS, 'categories'] as const,
  detail: (id: number) => [...ALL_KEYS, 'detail', id] as const,
}

export function useBlueprints(category?: string) {
  return useQuery({
    queryKey: KEYS.list(category),
    queryFn: () => listBlueprints(category),
  })
}

export function useBlueprintCategories() {
  return useQuery({
    queryKey: KEYS.categories,
    queryFn: listBlueprintCategories,
  })
}

export function useBlueprint(id: number | null) {
  return useQuery({
    queryKey: KEYS.detail(id!),
    queryFn: () => getBlueprint(id!),
    enabled: id !== null,
  })
}

export function useCreateBlueprint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: RoleBlueprintCreate) => createBlueprint(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}

export function useUpdateBlueprint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: RoleBlueprintUpdate }) => updateBlueprint(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}

export function useDeleteBlueprint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteBlueprint(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}
