import { useQuery } from '@tanstack/react-query'
import { fetchAppeal, fetchAppeals } from '../api/appeals'
import type { AppealFilters } from '../types/appeal'

export function useAppeals(filters: AppealFilters = {}) {
  return useQuery({
    queryKey: ['appeals', filters],
    queryFn: () => fetchAppeals(filters),
  })
}

export function useAppeal(id: number) {
  return useQuery({
    queryKey: ['appeal', id],
    queryFn: () => fetchAppeal(id),
    enabled: Number.isFinite(id),
  })
}
